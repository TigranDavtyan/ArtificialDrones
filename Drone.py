import cv2
import numpy as np
class Drone:
    def __init__(self,position,colour,index,game,mind=0):
        self.pos = position[:2]#x,y
        self.angle = position[2]+0.1#angle
        self.light = False
        self.colour = colour
        self.size = 15
        self.mind = mind
        self.memory = []
        self.detect_radius = 50
        self.epsilion = 1
        self.discount = 0.99
        self.index = index
        self.exists = True
        
        self.energy = 100
        self.energy_discount = 0.05
        self.ammo = 10
        
        self.move_step = 1
        self.rotation_step = 5

        self.game = game

    def move(self,actions):
        if self.energy <= 0:
            #print('Energia chka')
            self.exists = False
        if actions[2] == 1:
            self.angle += self.rotation_step
            self.energy -= self.energy_discount/10
        elif actions[2] == 2:
            self.angle -= self.rotation_step
            self.energy -= self.energy_discount/10
        self.angle %= 360
        angle = self.angle*(np.pi/180.)
        if actions[0] == 1:
            self.pos[0] += self.move_step * np.cos(angle)
            self.pos[1] -= self.move_step * np.sin(angle)
            self.energy -= self.energy_discount
        if actions[0] == 2:
            self.pos[0] -= self.move_step * np.cos(angle)
            self.pos[1] += self.move_step * np.sin(angle)
            self.energy -= self.energy_discount
            
        if actions[1] == 1:
            self.pos[0] += self.move_step * np.cos(angle-90*np.pi/180.)
            self.pos[1] -= self.move_step * np.sin(angle-90*np.pi/180.)
            self.energy -= self.energy_discount
        if actions[1] == 2:
            self.pos[0] += self.move_step * np.cos(angle+90*np.pi/180.)
            self.pos[1] -= self.move_step * np.sin(angle+90*np.pi/180.)
            self.energy -= self.energy_discount
            
        if actions[4] == 1:
            self.fire()    
        self.light = actions[3]
    
    def fire(self):
        if self.ammo > 0:
            self.game.bullets.append([self.pos[0],self.pos[1],self.angle])#TODO add random accuracy error when moving
            self.ammo -= 1
        
    def update(self):
        #state = normalise_position(self.pos) + [1 if self.light else -1,]
        #decision = mind.predict(state)
        #        0                   1                      2                         3               4          
        # 0     1       2     | 3    4    5   | 6      7            8         |   9         10    | 11   12
        #nop forward backward |nop left right |nop clockwise counterclockwise |light off  light on| nop fire
        if self.colour == 'blue':
            key = cv2.waitKey(20)
            if key == 119:
                actions = [1,0,0,0,0]
            elif key == 97:
                actions = [0,2,0,0,0]
            elif key == 100:
                actions = [0,1,0,0,0]
            elif key == 115:
                actions = [2,0,0,0,0]
            elif key == 113:
                actions = [0,0,1,0,0]
            elif key == 101:
                actions = [0,0,2,0,0]
            elif key == 32:
                actions = [0,0,0,0,1]
            else: return key
        else:
            if np.random.random() <= self.epsilion:
                actions = [np.random.randint(3),np.random.randint(3),np.random.randint(3),np.random.randint(2),np.random.randint(2)]
            actions[0] = 1
            actions[4] = 0
        #else:
        #    actions = [np.argmax(decision[:3]),np.argmax(decision[3:6]),np.argmax(decision[6:9]),np.argmax(decision[9:11]),np.argmax(decision[11:])]
        # 
        #self.memory.append([state,decision,actions,0])
        self.move(actions)
        if self.pos[0] < 0 or self.pos[0] > self.game.field.shape[1] or self.pos[1] < 0 or self.pos[1] > self.game.field.shape[0]:
            print('Chaperic durs eka')
            self.exists = False
        for drone in self.game.drones:
            if drone.exists and self.index != drone.index and (self.pos[0] - drone.pos[0])**2 + (self.pos[1] - drone.pos[1])**2 < (self.size+drone.size)**2:
                print('Kpa urishin')
                self.exists = False
                drone.exists = False
   
    def show(self,field):
        colour = (255,0,0) if self.colour == 'blue' else (0,0,255)
        pos = (int(self.pos[0]),int(self.pos[1]))
        cv2.circle(field,pos,self.size,colour,2)
        cv2.line(field,pos,(pos[0] + int(self.size*np.cos(self.angle*np.pi/180) ),pos[1] + int(-self.size*np.sin(self.angle*np.pi/180))),colour,1)
        cv2.circle(field,(pos[0]+int(self.size*np.cos((self.angle+90)*np.pi/180)/2),pos[1]+int(-self.size*np.sin((self.angle+90)*np.pi/180)/2)),int(self.size/2),(0,255,100),self.light-1)
    
    def check_bullet_collision(self):
        for bullet in self.game.bullets:
            if self.pos[0] == bullet[0] and self.pos[1] == bullet[1]:
                continue
                
            x = bullet[0]
            y = self.game.field.shape[1] - bullet[1]
            k = np.tan(bullet[2]*np.pi/180)
            b = y-k*x

            posy = self.game.field.shape[1] - self.pos[1]
            posx = self.pos[0]
            delta_y = abs(k * posx + b - posy)
            delta_x = abs(posx - ((posy - b)/k))
            h = delta_y if np.isinf(delta_x) else delta_x if np.isinf(delta_y) else delta_x*delta_y/np.sqrt(delta_x**2 + delta_y**2)

            if h < self.size:
                if ((bullet[2] >270 or bullet[2]<90) and (posy - b)/k < bullet[0]) or (bullet[2] <270 and bullet[2]>90) and (posy - b)/k > bullet[0]:
                    print('Chkpav')
                    continue
                print('Kpav!!!')
                self.exists = False