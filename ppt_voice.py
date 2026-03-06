import win32com.client

class PowerPointVoiceController:
    def __init__(self):
        self.ppt = None
        self.presentation = None
        self.slideshow = None

    def open_powerpoint(self):
        self.ppt = win32com.client.Dispatch("PowerPoint.Application")
        self.ppt.Visible = True
        print("[PPT] PowerPoint Opened")

    def create_new_presentation(self):
        if not self.ppt:
            self.open_powerpoint()

        self.presentation = self.ppt.Presentations.Add()
        print("[PPT] New Presentation Created")

    def add_slide(self, topic):
        if not self.presentation:
            self.create_new_presentation()

        slide_layout = 1  # Title and Content
        slide = self.presentation.Slides.Add(
            self.presentation.Slides.Count + 1,
            slide_layout
        )

        slide.Shapes.Title.TextFrame.TextRange.Text = topic.title()

        content = f"""
• Introduction to {topic}
• Key Concepts
• Applications
• Advantages
• Conclusion
"""

        slide.Shapes.Placeholders(2).TextFrame.TextRange.Text = content
        print(f"[PPT] Slide added on {topic}")

    def start_slideshow(self):
        if self.presentation:
            self.slideshow = self.presentation.SlideShowSettings.Run()
            print("[PPT] Slideshow Started")

    def next_slide(self):
        if self.ppt and self.ppt.SlideShowWindows.Count > 0:
            self.ppt.SlideShowWindows(1).View.Next()
            print("[PPT] Next Slide")

    def previous_slide(self):
        if self.ppt and self.ppt.SlideShowWindows.Count > 0:
            self.ppt.SlideShowWindows(1).View.Previous()
            print("[PPT] Previous Slide")
