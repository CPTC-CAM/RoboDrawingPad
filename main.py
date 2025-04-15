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

    # Properties to store the origin and maximum points for the robot drawing area
    x_origin = -336 # Top left X coordinate of the drawing area
    y_origin = -371 # Top left Y coordinate of the drawing area
    z_origin = 60 # Z coordinate to hover marker above drawing area

    x_max = 282  # Right border X coordinate of the drawing area
    y_max = -545 # Bottom border Y coordinate of the drawing area
    z_max = 40   # Z coordinate to place marker on drawing area

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

    def map_coordinates_to_robot_drawing_area(self, lines):
        """Map coordinates from the canvas to the robot drawing area, reversing Y axis."""
        mapped_points = []
        canvas_width = 800
        canvas_height = 600

        for line in lines:
            x, y = map(int, line.strip().split(","))

            # Preserve the 0,0 point (used as a pen lift marker)
            if x == 0 and y == 0:
                mapped_points.append((0, 0))
                continue

            # Linear interpolation for X
            x_mapped = int(self.x_origin + (x / canvas_width) * (self.x_max - self.x_origin))
            # Reverse Y axis: canvas Y=0 is top, robot Y=origin is top, but robot Y increases downward (or vice versa)
            y_mapped = int(self.y_origin + ((canvas_height - y) / canvas_height) * (self.y_max - self.y_origin))
            mapped_points.append((x_mapped, y_mapped))

        return mapped_points
    
    def save_points(self):
        """Save the points to a text file."""
        with open("points.txt", "w") as file:
            for x, y in self.points:
                file.write(f"{x},{y}\n")

        messagebox.showinfo("Save Points", "Points have been saved successfully!")
    
    async def draw_with_robot(self):
        """Placeholder for the 'Draw with Robot' functionality."""
        messagebox.showinfo("Robot Drawing...", "Draw starting...")
        await self.execDraw()

    # self added as a parameter to the function to be able to call it from the button
    async def execDraw(self):
        # Connect to your Nova instance (or use .env file)
        # Load environment variables from .env file
        load_dotenv()

        # Retrieve host and access token from environment variables
        # host = os.getenv("NOVA_API")
        # access_token = os.getenv("NOVA_ACCESS_TOKEN")

        # Use local instance with IP, username and password
        nova = Nova(
            host = os.getenv("HOST"),
            username = os.getenv("USERNAME"),
            password = os.getenv("PASSWORD"),
        )

        async with nova:
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
                actions = []

                print("Starting robot drawing...")
                # Loop through points from points.txt and add coordinates to robot action plan
                with open("points.txt", "r") as file:
                    lines = file.readlines()
                    lines = self.map_coordinates_to_robot_drawing_area(lines)
                    
                    pen_lifted = True
                    for line in lines:
                        x, y = line
                        if x == 0 and y == 0:
                            pen_lifted = True
                            # Move the z coordinate to the maximum value to lift the pen
                            actions.append(cartesian_ptp(current_pose @ Pose((0, 0, self.z_origin, 0, 0, 0))))
                        else:
                            # Move to the point (x, y) with a fixed z value

                            if pen_lifted:
                                # Move to the point (x, y) with the pen hovering above the drawing area
                                # and then move down to the drawing area
                                actions.append(cartesian_ptp(current_pose @ Pose((x, y, self.z_origin, 0, 0, 0))))
                                actions.append(cartesian_ptp(current_pose @ Pose((x, y, self.z_max, 0, 0, 0))))
                                pen_lifted = False
                            else:
                                actions.append(cartesian_ptp(current_pose @ Pose((x, y, self.z_origin, 0, 0, 0))))

                print("Executing robot drawing...")
                trajectory = await motion_group.plan(actions, tcp)
                await motion_group.execute(trajectory, tcp, actions)

                print("Robot drawing completed.")

if __name__ == "__main__":
    root = tk.Tk()
    app = DrawingApp(root)
    root.mainloop()
    print("All done!")