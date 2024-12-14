import gradio as gr
import pandas as pd
from qa_chatbot import PaysokoQA
from qa_logger import QALogger


class PaysokoGradioApp:
    def __init__(self):
        self.qa = PaysokoQA()
        self.logger = QALogger()

    def chat(self, message, tone, history):
        """Handle chat interactions"""
        history = history or []
        response = self.qa.ask(message, tone)
        self.logger.log_qa(message, response)
        history.append([message, response])
        return history, history

    def load_logs(self):
        """Load and format chat logs"""
        try:
            df = pd.read_csv("qa_logs.csv")
            styled_html = f"""
            <div style="background-color: #1f2937; color: white; padding: 20px;">
                {df.to_html(index=False, classes="styled-table")}
            </div>
            """
            return styled_html
        except Exception as e:
            return f"Error loading logs: {str(e)}"

    def create_interface(self):
        """Create Gradio interface"""
        custom_css = """
        .dark {
            background-color: #1f2937;
            color: white;
        }
        .message.bot {
            background-color: #374151 !important;
            color: white !important;
        }
        .message.user {
            background-color: #4B5563 !important;
            color: white !important;
        }
        .styled-table {
            width: 100%;
            border-collapse: collapse;
            margin: 25px 0;
            font-size: 0.9em;
            min-width: 400px;
            background-color: #374151;
            color: white;
        }
        .styled-table th,
        .styled-table td {
            padding: 12px 15px;
            border: 1px solid #4B5563;
        }
        """

        with gr.Blocks(
            title="Paysoko Customer Service",
            theme=gr.themes.Soft(
                primary_hue="blue",
                secondary_hue="blue",
                neutral_hue="slate",
                text_size=gr.themes.sizes.text_md,
            ),
            css=custom_css
        ) as interface:
            gr.Markdown("# Paysoko Customer Service Assistant")

            with gr.Tabs():
                with gr.Tab("Chat"):
                    chatbot = gr.Chatbot(
                        [],
                        height=600,
                        show_label=False,
                        avatar_images=[
                            "https://www.google.com/imgres?q=paysoko&imgurl=https%3A%2F%2Flookaside.fbsbx.com%2Flookaside%2Fcrawler%2Fmedia%2F%3Fmedia_id%3D106357797598805&imgrefurl=https%3A%2F%2Fwww.facebook.com%2FPaySoko%2F&docid=wL48e_8qKu4oAM&tbnid=ozJAzRmrubxC6M&vet=12ahUKEwi6t6KgoaeKAxUwVKQEHf6bCG0QM3oECHYQAA..i&w=2048&h=1365&hcb=2&ved=2ahUKEwi6t6KgoaeKAxUwVKQEHf6bCG0QM3oECHYQAA",  # Replace with actual path or URL
                            "https://www.google.com/imgres?q=paysoko&imgurl=https%3A%2F%2Flookaside.fbsbx.com%2Flookaside%2Fcrawler%2Fmedia%2F%3Fmedia_id%3D106357797598805&imgrefurl=https%3A%2F%2Fwww.facebook.com%2FPaySoko%2F&docid=wL48e_8qKu4oAM&tbnid=ozJAzRmrubxC6M&vet=12ahUKEwi6t6KgoaeKAxUwVKQEHf6bCG0QM3oECHYQAA..i&w=2048&h=1365&hcb=2&ved=2ahUKEwi6t6KgoaeKAxUwVKQEHf6bCG0QM3oECHYQAA"    # Replace with actual path or URL
                        ],
                        bubble_full_width=False,
                        render_markdown=True
                    )
                    state = gr.State([])

                    with gr.Row():
                        msg = gr.Textbox(
                            label="Ask a question",
                            placeholder="Type your question here...",
                            scale=3,
                            container=False
                        )
                        tone = gr.Dropdown(
                            choices=[
                                "Professional and formal",
                                "Friendly and helpful",
                                "Brief and direct",
                                "Detailed and explanatory"
                            ],
                            label="Select tone",
                            value="Professional and formal",
                            scale=1,
                            container=False
                        )

                    with gr.Row():
                        submit = gr.Button("Send", variant="primary")
                        clear = gr.Button("Clear", variant="secondary")

                with gr.Tab("Logs"):
                    logs_display = gr.HTML()
                    refresh_btn = gr.Button("Refresh Logs", variant="primary")

            # Event handlers remain the same
            msg.submit(
                self.chat,
                inputs=[msg, tone, state],
                outputs=[chatbot, state]
            ).then(lambda: "", None, msg)

            submit.click(
                self.chat,
                inputs=[msg, tone, state],
                outputs=[chatbot, state]
            ).then(lambda: "", None, msg)

            clear.click(lambda: ([], []), None, [chatbot, state])
            refresh_btn.click(self.load_logs, None, logs_display)
            interface.load(self.load_logs, None, logs_display)

        return interface


if __name__ == "__main__":
    app = PaysokoGradioApp()
    interface = app.create_interface()
    interface.launch(
        server_name="0.0.0.0",
        server_port=7860,
        share=True
    )
