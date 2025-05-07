
import  ursina
app = ursina.Ursina()

player = ursina.Entity(model='cube', color=ursina.color.red, scale=(1, 2, 1))
player.position = (0, 0, 0)

ground = ursina.Entity(model='cube', color=ursina.color.green, scale=(10, 0.1, 10))
ground.position = (0, -1, 0)

obstacles = []
for i in range(10):
    obstacle = ursina.Entity(model='cube', color=ursina.color.blue, scale=(1, 1, 1))
    obstacle.position = (i * 2, 0, 0)
    obstacles.append(obstacle)

def update(): 
    player.x += ursina.held_keys['d'] * 0.1
    player.x -= ursina.held_keys['a'] * 0.1

    if player.intersects().hit:
        player.color = ursina.color.red
    else:
        player.color = ursina.color.red

    for obstacle in obstacles:  
        if player.intersects(obstacle).hit:
            player.color = ursina.color.red
            ursina.destroy(obstacle)
            obstacles.remove(obstacle)
            break
        else:
            player.color = ursina.color.red

app.run()
