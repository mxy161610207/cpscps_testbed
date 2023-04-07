import tkinter as tk

class App:
    def __init__(self, root, E):
        self.root = root
        self.E = E
        self.canvas = tk.Canvas(root, width=300, height=300, bg='white')
        self.canvas.pack()
        self.draw_axes()
        self.draw_square()
        
    def draw_axes(self):
        x = self.canvas.winfo_width() // 2
        y = self.canvas.winfo_height() // 2
        self.canvas.create_line(0, y, self.canvas.winfo_width(), y)
        self.canvas.create_line(x, 0, x, self.canvas.winfo_height())

    def draw_square(self):
        x = self.canvas.winfo_width() // 2
        y = self.canvas.winfo_height() // 2
        s = self.E // 2
        self.canvas.create_rectangle(x - s, y - s, x + s, y + s)
        
    def draw_arrow(self, x, y, a):
        x0 = self.canvas.winfo_width() // 2 + x - a // 2
        y0 = self.canvas.winfo_height() // 2 - y - a // 2
        x1 = x0 + a
        y1 = y0 + a
        self.canvas.create_line(x0, y0, x1, y0, arrow=tk.LAST)
    
    def update(self, x, y, a):
        self.draw_arrow(x, y, a)

# test
root = tk.Tk()
app = App(root, E=100)
app.update(50, 30, 20)
root.mainloop()
