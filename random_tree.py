import turtle
import random

def draw_branch(branch_length, depth):
    if depth == 0:
        return
    
    angle = random.randint(15, 45)
    reduction = random.uniform(0.6, 0.8) # Reduce branch length by 60% to 80%
    
    turtle.forward(branch_length)
    turtle.right(angle)
    draw_branch(branch_length * reduction, depth - 1)
    
    turtle.left(angle * 2)
    draw_branch(branch_length * reduction, depth - 1)
    
    turtle.right(angle)
    turtle.backward(branch_length)

def draw_tree(depth):
    turtle.left(90) # Point the turtle upwards
    turtle.color("brown")
    draw_branch(100, depth)
    turtle.done()

turtle.speed(0) # Set turtle drawing to the fastest
draw_tree(depth=5) # Change the depth as needed