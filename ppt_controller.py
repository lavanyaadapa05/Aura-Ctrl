import win32com.client

class PPTController:
    def __init__(self):
        self.ppt = None
        self.presentation = None

    # Connect to PowerPoint (open or already running)
    def connect_powerpoint(self):
        try:
            # Try connecting to already running PowerPoint
            self.ppt = win32com.client.GetActiveObject("PowerPoint.Application")
            print("[PPT] Connected to existing PowerPoint")
        except:
            # If not running, open new instance
            self.ppt = win32com.client.Dispatch("PowerPoint.Application")
            self.ppt.Visible = True
            print("[PPT] PowerPoint Opened")

        self.ppt.Visible = True

    # Get active presentation if already open
    def get_active_presentation(self):
        self.connect_powerpoint()

        if self.ppt.Presentations.Count > 0:
            self.presentation = self.ppt.ActivePresentation
            print("[PPT] Using Active Presentation")
        else:
            print("[PPT] No presentation open")

    # Create new presentation
    def create_new_presentation(self):
        self.connect_powerpoint()
        self.presentation = self.ppt.Presentations.Add()
        print("[PPT] New Presentation Created")

    # Add slide to current presentation
    def add_slide(self, topic):
        self.get_active_presentation()

        if not self.presentation:
            print("[PPT] No active presentation found")
            return

        slide_layout = 1  # Title + Content
        slide = self.presentation.Slides.Add(
            self.presentation.Slides.Count + 1,
            slide_layout
        )

        slide.Shapes.Title.TextFrame.TextRange.Text = topic.title()

        content = (
            f"• Introduction to {topic}\n"
            f"• Key Concepts\n"
            f"• Applications\n"
            f"• Advantages\n"
            f"• Conclusion"
        )

        slide.Shapes.Placeholders(2).TextFrame.TextRange.Text = content

        print(f"[PPT] Slide Added: {topic}")

    # Start slideshow (works for existing PPT too)
    def start_slideshow(self):
        self.connect_powerpoint()

        if self.ppt.Presentations.Count > 0:
            presentation = self.ppt.ActivePresentation
            if presentation.Slides.Count > 0:
                presentation.SlideShowSettings.Run()
                print("[PPT] Slideshow Started")
            else:
                print("[PPT] No slides in presentation")
        else:
            print("[PPT] No presentation open")

    # Next slide
    def next_slide(self):
        self.connect_powerpoint()

        if self.ppt.SlideShowWindows.Count > 0:
            self.ppt.SlideShowWindows(1).View.Next()
            print("[PPT] Next Slide")

    # Previous slide
    def previous_slide(self):
        self.connect_powerpoint()

        if self.ppt.SlideShowWindows.Count > 0:
            self.ppt.SlideShowWindows(1).View.Previous()
            print("[PPT] Previous Slide")

        # Stop slideshow
    def stop_slideshow(self):
        self.connect_powerpoint()

        if self.ppt.SlideShowWindows.Count > 0:
            self.ppt.SlideShowWindows(1).View.Exit()
            print("[PPT] Slideshow Stopped")
        else:
            print("[PPT] No active slideshow")
