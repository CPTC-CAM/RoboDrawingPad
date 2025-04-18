import tkinter as tk
from tkinter import messagebox

from nova import Nova
from nova import api
from nova.actions import cartesian_ptp, joint_ptp
from nova.types import Pose

import asyncio

import os
from dotenv import load_dotenv

class DrawingApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Robo Drawing Pad")
        
        # Canvas setup
        self.canvas = tk.Canvas(root, width=800, height=600, bg="white")
        self.canvas.pack()
        
        # Initialize variables
        self.drawing = False
        self.points = []  # List to store x, y points
        
        # Bind mouse events
        self.canvas.bind("<ButtonPress-1>", self.start_drawing)
        self.canvas.bind("<B1-Motion>", self.draw)
        self.canvas.bind("<ButtonRelease-1>", self.stop_drawing)
        
        # Add a button to clear the canvas
        self.clear_button = tk.Button(root, text="Clear", command=self.clear_canvas)
        self.clear_button.pack(pady=10)
        
        # Add a button to save points to a text file
        self.save_button = tk.Button(root, text="Save Points", command=self.save_points)
        self.save_button.pack(pady=10)
        
        self.robot_button = tk.Button(root, text="Draw with Robot", command=lambda: root.after(0, asyncio.run(self.draw_with_robot())))
        self.robot_button.pack(pady=10)
    
    def start_drawing(self, event):
        """Start capturing points when the user presses the mouse button."""
        self.drawing = True
        self.points.append((event.x, event.y))  # Capture the starting point
    
    def draw(self, event):
        """Draw on the canvas and capture points as the user moves the mouse."""
        if self.drawing:
            # Draw a line from the last point to the current point
            if self.points:
                x_prev, y_prev = self.points[-1]
                self.canvas.create_line(x_prev, y_prev, event.x, event.y, fill="black", width=2)
            self.points.append((event.x, event.y))  # Capture the current point
    
    def stop_drawing(self, event):
        """Stop capturing points when the user releases the mouse button."""
        # Add a 0, 0 coordinate to the file to indicate the end of the drawing session
        # this will create a point where the robot can lift up the pen
        if self.drawing:
            self.points.append((0, 0))
        self.drawing = False
    
    def clear_canvas(self):
        """Clear the canvas and reset the points list."""
        self.canvas.delete("all")
        self.points = []
    
    def save_points(self):
        """Save the points to a text file."""
        with open("points.txt", "w") as file:
            for x, y in self.points:
                file.write(f"{x},{y}\n")

        messagebox.showinfo("Save Points", "Points have been saved successfully!")
    
    async def draw_with_robot(self):
        """Placeholder for the 'Draw with Robot' functionality."""
        messagebox.showinfo("Robot Drawing...", "Draw with Robot functionality will be implemented later.")
        await self.execDraw()

    # self added as a parameter to the function to be able to call it from the button
    async def execDraw(self):
        # Connect to your Nova instance (or use .env file)
        # Load environment variables from .env file
        load_dotenv()

        # Retrieve host and access token from environment variables
        # host = os.getenv("NOVA_API")
        # access_token = os.getenv("NOVA_ACCESS_TOKEN")

        nova = Nova(
            host="hostnameorIPhere",
            username="yourusername",
            password="yourpassword",
        )

        async with Nova() as nova:
            cell = nova.cell()
            controller = await cell.ensure_virtual_robot_controller(
                "myvirtualbot",
                "universalrobots-ur5cb",
                "universalrobots"
            )

            # Define starting positions
            async with controller[0] as motion_group:
                tcp = "Flange"
                home_joints = await motion_group.joints()
                current_pose = await motion_group.tcp_pose(tcp)

                # Movement actions
                actions = [
                    joint_ptp(home_joints),
                    cartesian_ptp(current_pose @ Pose((200, 0, 0, 0, 0, 0))),
                    joint_ptp(home_joints)
                ]

                trajectory = await motion_group.plan(actions, tcp)
                await motion_group.execute(trajectory, tcp, actions)

        await nova.close()

if __name__ == "__main__":
    root = tk.Tk()
    app = DrawingApp(root)
    root.mainloop()
    print("All done!")