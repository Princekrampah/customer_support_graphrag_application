from dotenv import load_dotenv
import os
from langchain_anthropic import ChatAnthropic
from pydantic import BaseModel, Field, field_validator
from typing import List, Union, Optional
from langchain.prompts import ChatPromptTemplate
from langchain_community.graphs import Neo4jGraph
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnablePassthrough
from langchain.chains.graph_qa.cypher_utils import CypherQueryCorrector, Schema


class PaysokoEntities(BaseModel):
    """Identifying information about Paysoko entities."""
    office_locations: Union[List[str], None] = Field(
        default_factory=list,
        description="Python List object all office locations mentioned in the text (e.g. ['LOC001', 'Paysoko CBD'])"
    )
    services: Union[List[str], None] = Field(
        default_factory=list,
        description="Python List object all payment services mentioned in the text (e.g. ['PS001', 'Money Transfer'])"
    )
    appointments: Union[List[str], None] = Field(
        default_factory=list,
        description="Python List object of all appointments mentioned in the text (e.g. ['APT001'])"
    )
    office_hours: Union[List[str], None] = Field(
        default_factory=list,
        description="Python List object of office hours mentioned (e.g. ['opening_time', 'closing_time', 'monday'])"
    )

    @field_validator('office_locations', 'services', 'appointments', 'office_hours')
    def validate_list_fields(cls, v, info):
        if v is None:
            return []
        if isinstance(v, str):
            print(v)
            v = v.strip('[]').replace("'", "").split(', ')
            return [item.strip() for item in v if item.strip()]
        if isinstance(v, list):
            return v
        return list(v)

    class Config:
        arbitrary_types_allowed = True


class PaysokoQA:
    def __init__(self):
        load_dotenv()
        self.model = ChatAnthropic(model='claude-3-opus-20240229')
        self.graph = Neo4jGraph()
        self.setup_chains()

    def setup_chains(self):
        # Entity extraction chain
        prompt = ChatPromptTemplate.from_messages([
            (
                "system",
                "You are extracting office locations, services, appointments, and operating hours from Paysoko text queries. Do always return full Python objects that are synthatically correct."
            ),
            (
                "human",
                "Use the given format to extract information from the following input: {question}"
            ),
        ])
        self.entity_chain = prompt | self.model.with_structured_output(
            PaysokoEntities)

        # Cypher generation chain
        cypher_template = """Based on the Paysoko Neo4j graph schema below, write a Cypher query that would answer the user's question:

       {schema}

       The entities mentioned in the question map to these database values:
       {entities_list}

       User Question: {question}

       Write a Cypher query to answer this question.
       Note: Focus only on Appointments, Services, OfficeLocations and Office Hours relationships.

       Cypher query:"""

        cypher_prompt = ChatPromptTemplate.from_messages([
            (
                "system",
                "Generate a Cypher query to get information from the Paysoko database. Return only the query without explanation."
            ),
            ("human", cypher_template),
        ])

        self.cypher_response = (
            RunnablePassthrough.assign(entities=self.entity_chain) |
            RunnablePassthrough.assign(
                entities_list=lambda x: self.map_to_database(x["entities"]),
                schema=lambda _: self.graph.get_schema,
            ) |
            cypher_prompt |
            self.model.bind(stop=["\nResult:"]) |
            StrOutputParser()
        )

        # Schema validation
        corrector_schema = [
            Schema(el["start"], el["type"], el["end"])
            for el in self.graph.structured_schema.get("relationships")
        ]
        self.cypher_validation = CypherQueryCorrector(corrector_schema)

        # Response generation chain
        response_template = """
       Based on the question, Cypher query, and database response, provide a natural language answer in markdown format:

       Question: {question}
       Cypher query: {query} 
       Database Response: {response}

       Response should focus on:
       - Office locations and working hours
       - Available services and costs
       - Appointment details and scheduling
       
       The tone of voice you should use in your final response:
       {tone_of_voice}
       """

        response_prompt = ChatPromptTemplate.from_messages([
            (
                "system",
                "You are a customer service assistant for Paysoko. Provide clear, direct answers based on the query results."
            ),
            ("human", response_template),
        ])

        self.chain = (
            RunnablePassthrough.assign(query=self.cypher_response) |
            RunnablePassthrough.assign(
                response=lambda x: self.graph.query(
                    self.cypher_validation(x["query"]))
            ) |
            response_prompt |
            self.model |
            StrOutputParser()
        )

    def map_to_database(self, entities: PaysokoEntities) -> Optional[str]:
        fulltext_query = """
       CALL db.index.fulltext.queryNodes($indexName, $value) 
       YIELD node, score
       WITH node, score, labels(node)[0] AS type
       RETURN 
           CASE type
               WHEN 'OfficeLocation' THEN node.location_name
               WHEN 'Services' THEN node.service_name
               WHEN 'Appointment' THEN node.appointment_id
           END AS result,
           type,
           score
       ORDER BY score DESC
       LIMIT 1
       """

        hours_query = """
       MATCH (h:OfficeHour)
       WHERE h.day_of_week = $time OR h.opening_time = $time OR h.closing_time = $time
       RETURN 
           h.day_of_week + ' ' + h.opening_time + '-' + h.closing_time as result,
           'OfficeHour' as type,
           1.0 as score
       LIMIT 1
       """

        result = ""

        for entity_type, entity_list in [
            ("locationIndex", entities.office_locations),
            ("serviceIndex", entities.services),
            ("appointmentIndex", entities.appointments)
        ]:
            for entity in entity_list:
                try:
                    response = self.graph.query(fulltext_query, {
                        "indexName": entity_type,
                        "value": entity
                    })
                    if response and len(response) > 0:
                        result += (f"{entity} maps to {response[0]['result']} "
                                   f"({response[0]['type']}) with score "
                                   f"{response[0]['score']:.2f}\n")
                    else:
                        result += f"No match found for {entity}\n"
                except Exception as e:
                    print(f"Error mapping entity {entity}: {e}")

        for time in entities.office_hours:
            try:
                response = self.graph.query(hours_query, {"time": time})
                if response and len(response) > 0:
                    result += (f"{time} maps to {response[0]['result']} "
                               f"({response[0]['type']}) with score "
                               f"{response[0]['score']:.2f}\n")
                else:
                    result += f"No match found for {time}\n"
            except Exception as e:
                print(f"Error mapping office hour {time}: {e}")

        return result if result else None

    def ask(self, question: str, tone_of_voice: str) -> str:
        """Main method to ask questions"""
        return self.chain.invoke({"question": question, "tone_of_voice": tone_of_voice})

    async def a_ask(self, question: str, tone_of_voice: str) -> str:
        """Main method to ask questions asynchronously"""
        response = await self.chain.ainvoke({"question": question, "tone_of_voice": tone_of_voice})
        return response
