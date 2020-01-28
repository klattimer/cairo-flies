"""
This program is free software; you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation; version 2 of the License.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

Copyright Karl Lattimer 2008
"""
import gtk
import gobject
import cairo
import pangocairo
import pango
import random
import rsvg
import math


class Timer:
    def __init__(self, time, callback):
        self.__time = time
        self.__callback = callback
        self.__timeout_id = None

    def start(self):
        if self.__timeout_id == None:
            self.__timeout_id = gobject.timeout_add(self.__time, self.__callback)
            return True
        return False

    def stop(self):
        if self.__timeout_id != None:
            gobject.source_remove(self.__timeout_id)
            self.__timeout_id = None
            return True
        return False

    def restart(self):
        self.stop()
        self.start()

class Fly:
    def __init__( self, swarm, max_speed ):
        self.swarm = swarm
        self.max_speed = max_speed
        self.max_neighbours = 3
        self.direction_x = 0
        self.direction_y = 0
        self.x = random.randint(0, self.swarm.width)
        self.y = random.randint(0, self.swarm.height)
        self.velocity_x = random.randint(-1*self.max_speed, self.max_speed)
        self.velocity_y = random.randint(-1*self.max_speed, self.max_speed)
        self.tail_x = 0
        self.tail_y = 0
        self.neighbours = []
        self.target = None
        self.target_tracks = 0
        self.track_limit = 3
        self.child_counter = 0
        self.child_food_limit = 1
	self.num_of_flies = self.swarm.CountFlies()
        self._add_neighbour()

        self.eyes = []
        self.view_distance = 90
        if len(self.eyes) < 1:
            self.eyes.append((0, 60))
        if len(self.eyes) > 1:
            self.eyes = []
            self.eyes.append((0, 60))

    def ReplaceNeighbour(self, old_fly, new_fly=None):
        self.num_of_flies = self.swarm.CountFlies()
        self._del_neighbour(old_fly)
        self._add_neighbour(new_fly)

    def ReplaceRandom( self, hit=None ):
        self.num_of_flies = self.swarm.CountFlies()
        if not hit:
            hit = random.randint(0, len(self.neighbours))
        for index, neighbour in enumerate(self.neighbours):
            if index == hit:
                self.neighbours[index] = random.randint(0, self.num_of_flies)

    def Move( self, x=None, y=None ):
        if not x:
            x = self.x+self.velocity_x
        if not y:
            y = self.y+self.velocity_y
        self.tail_x = self.x
        self.tail_y = self.y
        self.x = x
        self.y = y
        if len(self.neighbours) < self.max_neighbours:
            self._add_neighbour()

    def Hunt ( self, x, y ):
       for eye in self.eyes:
           (direction, fov) = eye
           (angle, length) = self._rtop(self.tail_x - self.x,
                                        self.tail_y - self.y, 
                                        True)
        
           lea = math.radians(angle + direction - fov/2)
           rea = math.radians(angle + direction + fov/2)

           (angle, length) = self._rtop(self.x - x , self.y - y)
           if int(length) < self.view_distance and lea < angle and rea > angle:
               if self.target:
                   #print "Target retained"
                   self.target_tracks = self.target_tracks + 1
               else:
                   #print "Target acquired"
                   self.target_tracks = 1
           else:
               if self.target:
                   #print "Target lost"
                   self.target_tracks = 0
               return False

           if self.target_tracks > self.track_limit:
               try:
                   if length < self.max_speed:
                       self.target.swarm._del_fly(self.target)
                       self.child_counter = self.child_counter + 1
                       self.swarm.total_devoured = self.swarm.total_devoured + 1
                       print "Target devoured %d" % self.child_counter
                   
                   if self.child_counter >= self.child_food_limit:
                       self.swarm._add_fly()
                       self.child_counter = 0;
               except:
                   self.target_tracks = 0
                   self.ReplaceRandom()
               return False
            
           dist_x = self.x - x
           dist_y = self.y - y

#           self.direction_x = (self.direction_x + (0.2 * (math.fabs(dist_x) / self.max_speed)))
#           self.direction_y = (self.direction_y + (0.2 * (math.fabs(dist_y) / self.max_speed)))

           if dist_x != 0:
               vx = self.velocity_x 
               self.velocity_x = vx + (0.2 * (math.fabs(dist_x)/dist_x))

           if self.velocity_x > self.max_speed:
               self.velocity_x = (math.fabs(self.velocity_x)/3)
           elif self.velocity_x < (-1*self.max_speed):
               self.velocity_x = (-1*(math.fabs(self.velocity_x)/3))
           
           if dist_y != 0:
               vy = self.velocity_y
               self.velocity_y = vy + (0.2 * (math.fabs(dist_y)/dist_y))

           if self.velocity_y > self.max_speed:
               self.velocity_y = (math.fabs(self.velocity_y)/3)
           elif self.velocity_y < (-1*self.max_speed):
               self.velocity_y = (-1*(math.fabs(self.velocity_y)/3))
           self.Move()
           return True

    def _add_neighbour(self, fly=None):
        if self.num_of_flies == 0:
            self.num_of_flies = self.swarm.CountFlies()
        if self.num_of_flies == 0:
            print "No other flies skipping neighbour association"
            return
        if len(self.neighbours) > self.max_neighbours:
            return

        if not fly:
            fly = random.randint(0, self.num_of_flies)
        self.neighbours.append(fly)
    
    def _del_neighbour(self, fly):
        try:
            self.neighbours.remove(fly)
        except:
            pass
            #print "Attempt to delete a non-existent neighbour %d" % fly

    def _rtop ( self, x, y, deg=False ):
        if deg:
            angle = 180.0 * math.atan2(y, x) / math.pi
            length = math.hypot(x, y)
        else: 
            angle = math.atan2(y, x)
            length = math.hypot(x, y)
        return (angle, length)

    def _ptor ( self, angle, length, deg=False ):
        if deg: 
            angle = math.pi * angle / 180.0 
        x = length * math.cos(angle)
        y =  length * math.sin(angle)
        return x, y

class Swarm:
    def __init__(self, widget, prey=None, num_of_flies=30):
	self.prey = prey
        self.flies = []
        self.widget = widget
        self.max_speed = 17
        if prey:
            self.max_speed = 16
        self.x_grav = 1
        self.y_grav = 3
        self.refresh_count = 0
	self.UpdateSize()
        self.total_added = -1 * num_of_flies
        self.total_deleted = 0;
	for fly in range(num_of_flies):
		self._add_fly()
	self.CountFlies()
        self.total_devoured = 0
	self.Refresh()

    def CountFlies( self ):
	self.num_of_flies = len( self.flies )
	return self.num_of_flies

    def UpdateSize( self ):
	self.width = self.widget.width
	self.height = self.widget.height

    def Refresh ( self ):
        self.refresh_count = self.refresh_count + 1
	self.CountFlies()
        nr = False
        ar = False
	for fly in self.flies:
            self._proximity(fly)
            self._hunt(fly)
#            self._evade()
            self._grav(fly)
            if self.refresh_count == 193 and not nr:
                fly.ReplaceRandom()
                nr = True
            if self.refresh_count == 265 and not ar:
                if not self.prey:
                    self._add_fly()
                    self._add_fly()
                    self._add_fly()
                    ar = True
            if self.refresh_count > 1023:
                #self._del_fly(fly)
                self.refresh_count = 0
            fly.Move()

    def SetColor( self, color ):
        self.color = color
    def _add_fly ( self ):
        print "Adding fly"
        self.total_added = self.total_added + 1
	self.flies.append( Fly( self, self.max_speed ) )

    def _del_fly ( self, fly ):
        print "Deleting fly"
        self.total_deleted = self.total_deleted + 1
        self.flies.remove(fly)

    def _proximity (self, fly):
	"""
        If the neighbours of this flys neighbours are closer then repatriate them
        to this fly.

	The implementation of this can be improved greatly
	"""
        for index, neighbour in enumerate(fly.neighbours):
            if neighbour > self.num_of_flies - 1:
                fly.ReplaceRandom(index)
                continue
            distance = self._distance(self.flies[neighbour-1], fly)
            for index, next_neighbour in enumerate(self.flies[neighbour-1].neighbours):
                if next_neighbour > self.num_of_flies - 1:
                    fly.ReplaceRandom(index)
                    continue
                next_distance  = self._distance(self.flies[next_neighbour-1], fly) 
                if next_distance > distance and next_neighbour != fly:
                    change = True
                    for t_neighbour in fly.neighbours:
                        if t_neighbour == next_neighbour:
                            change = False
                    if change:
                        fly.ReplaceNeighbour(neighbour, next_neighbour)

            dist_x = self.flies[neighbour-1].x - fly.x
            dist_y = self.flies[neighbour-1].y - fly.y

            if dist_x == 0:
                dist_x = 1
            if dist_y == 0:
                dist_y = 1

            fly.direction_x = (fly.direction_x + (0.1 * (math.fabs(dist_x) / self.max_speed)))/2
            fly.direction_y = (fly.direction_y + (0.1 * (math.fabs(dist_y) / self.max_speed)))/2

            if fly.direction_x > 1:
                fly.direction_x = 1
            elif fly.direction_x < -1:
                fly.direction_x = -1

            if fly.direction_y > 1:
                fly.direction_y = 1
            elif fly.direction_y < -1:
                fly.direction_y = -1

            # Calculate X velocity
            if dist_x != 0:
                vx = fly.velocity_x
                fly.velocity_x = vx + fly.direction_x * (math.fabs(dist_x)/dist_x)

            if fly.velocity_x > self.max_speed:
                fly.velocity_x = (math.fabs(fly.velocity_x)/2)
            elif fly.velocity_x < (-1*self.max_speed):
                fly.velocity_x = (-1*(math.fabs(fly.velocity_x)/2))

            # Calculate Y velocity
            if dist_y != 0:
                vy = fly.velocity_y
                fly.velocity_y = vy + fly.direction_y * (math.fabs(dist_y)/dist_y)

            if fly.velocity_y > self.max_speed:
                fly.velocity_y = (math.fabs(fly.velocity_y)/2)
            elif fly.velocity_y < (-1*self.max_speed):
                fly.velocity_y = (-1*(math.fabs(fly.velocity_y)/2))

    def _grav(self, fly):
	"""
	Fly gravity, gravity point is currently fixed at a distance of 
	two thirds width from centre. This is boxy and highly inaccurate 
	and just plain pants.

	A better way would be that gravity is determined as a function
	of the polar distance from the gravity target.

	The gravity target could then be determined by some other means

	"""
        if fly.x < self.width/6:
            fly.velocity_x = fly.velocity_x + random.randint(0, self.x_grav)
        if fly.x > self.width-(self.width/6):
            fly.velocity_x = fly.velocity_x - random.randint(0, self.x_grav)
        if fly.y < self.height/6:
            fly.velocity_y = fly.velocity_y + random.randint(0, self.y_grav)
        if fly.y > self.height-(self.height/6):
            fly.velocity_y = fly.velocity_y - random.randint(0, self.y_grav)

    def _hunt( self, fly ):
       if not self.prey:
           return

       if fly.target:
           hit = fly.Hunt(fly.target.x, fly.target.y)
           if hit:
               return
       fly.target = None
       for prey_fly in self.prey.flies:
           hit = fly.Hunt(prey_fly.x, prey_fly.y)
           if hit:
               fly.target = prey_fly
               break;

    def _kill( self, fly, kill ):
        pass

    def _distance ( self, a, b ):
        # I'm sure pythagoras is released under GPL
        x = a.x - b.x
        y = a.y - b.y
        return int(math.hypot(x, y))    

class FliesWidget(gtk.DrawingArea):
    __gsignals__ = {
        "expose-event": "override",
        "configure_event": "override",
    }

    def __init__ ( self, fps, width, height ):
        gtk.DrawingArea.__init__(self)
        self.swarms = []

        self.width = width
        self.height = height

	Swarm_a = Swarm( self, None, 40 )
        Swarm_a.SetColor((0.6, 0.2, 0.2))
	self.swarms.append(Swarm_a)

        Swarm_b = Swarm( self, Swarm_a, 40)
        Swarm_b.SetColor((0.2, 0.2, 0.6))

        Swarm_a.prey = Swarm_b
	self.swarms.append(Swarm_b)
        """
        Swarm_c = Swarm( self, Swarm_a, 22)
        Swarm_c.SetColor((0.2, 0.6, 0.2))
	self.swarms.append(Swarm_c)

        Swarm_d = Swarm( self, Swarm_b, 4)
        Swarm_d.SetColor((0.2, 0.6, 0.6))
	self.swarms.append(Swarm_d)

        Swarm_e = Swarm( self, Swarm_c, 8)
        Swarm_e.SetColor((0.6, 0.6, 0.2))
	self.swarms.append(Swarm_e)

        Swarm_f = Swarm( self, Swarm_e, 5)
        Swarm_f.SetColor((0.6, 0.3, 0.2))
	self.swarms.append(Swarm_f)

        Swarm_g = Swarm( self, Swarm_d, 15)
        Swarm_g.SetColor((0.6, 0.6, 0.2))

        Swarm_a.prey = Swarm_g

	self.swarms.append(Swarm_g)
        """
	self._timer = Timer(1000/fps, self._update)

    def do_configure_event ( self, event ):
        (self.width, self.height) = self.window.get_size()
        self._timer.start()
	self._update()

    def do_expose_event ( self, event ):
        self.width = event.area.width
        self.height = event.area.height
        self.cr = self.window.cairo_create()
	self._render()

    def _update( self ):
	for swarm in self.swarms:
            swarm.UpdateSize()
            swarm.Refresh()
	self.queue_draw()
        return True

    def _render ( self ):
	self.cr.set_source_rgba(1,1,1,1)
	self.cr.paint()

        title_offset = 15
	for swarm in self.swarms:
            (r, g, b) = swarm.color
            self.cr.set_source_rgb(r, g, b)
            self.cr.move_to(10, title_offset);
            self.cr.show_text("Swarm %d (%d, %d, %d)" % (len(swarm.flies), swarm.total_devoured, swarm.total_deleted, swarm.total_added))
            for fly in swarm.flies:
                self._render_fly(fly)
            title_offset = title_offset + 15;

    def _render_fly ( self, fly ):
        self.cr.save()
        (r, g, b) = fly.swarm.color

        # Draw the head
        self.cr.arc(fly.x, fly.y, 4, 0, 2.0 * math.pi)
        self.cr.set_line_width( 3 )
        self.cr.fill()
        self.cr.restore()
        
        self.cr.save()
        # Draw the tail
        if fly.tail_x == 0:
            fly.Move()
        (angle, length) = fly._rtop(fly.tail_x - fly.x,
                                     fly.tail_y - fly.y)
        fly.length = (length/2)+6
        (tail_x, tail_y) = fly._ptor(angle, fly.length)
        self.cr.set_source_rgb(r, g, b)
        self.cr.set_line_width( 3 )
        self.cr.move_to( tail_x+fly.x, tail_y+fly.y )        
        self.cr.line_to( fly.x, fly.y )
        self.cr.stroke()
        self.cr.restore()
        
        if fly.target:
            self.cr.save()
            self.cr.set_source_rgba(1, 0.2, 0.2, 0.3)
            self.cr.arc(fly.x, fly.y, 3, 0, 2.0 * math.pi)
            self.cr.stroke()
            self.cr.restore()

            self.cr.save()
            self.cr.set_source_rgba(1, 0.2, 0.2, 0.3)
            self.cr.move_to (fly.x, fly.y)
            self.cr.line_to (fly.target.x, fly.target.y)
            self.cr.stroke()
            self.cr.restore()

            self.cr.save()
            self.cr.set_source_rgba(1, 0.2, 0.2, 0.3)
            self.cr.arc(fly.target.x, fly.target.y, 7, 0, 2.0 * math.pi)
            self.cr.stroke()
            self.cr.restore()

        
        self.cr.save()        
        self.cr.set_source_rgba(b, r, g, .05)    
        
        #for eye in fly.eyes:
            # Draw the visual range
        #    (direction, fov) = eye
        #    (angle, length) = fly._rtop(fly.x - fly.tail_x,
        #                            fly.y - fly.tail_y, 
        #                            True)
        
        #    lea = math.radians(angle + direction - fov/2)
        #    rea = math.radians(angle + direction + fov/2)

        #    (lex, ley) = fly._ptor(lea, fly.view_distance)
        #    (rex, rey) = fly._ptor(rea, fly.view_distance)
                
        #    #self.cr.move_to( fly.x, fly.y)
        #    self.cr.line_to( lex+fly.x, ley+fly.y )
        
        #    self.cr.arc(fly.x, fly.y, fly.view_distance, lea, rea)
        
        #    self.cr.move_to( rex+fly.x, rey+fly.y)        
        #    self.cr.line_to( fly.x, fly.y )
        #    self.cr.fill_preserve()
        #    self.cr.stroke()
        self.cr.restore()
        
if __name__ == "__main__":
    window = gtk.Window()
    window.connect("delete-event", gtk.main_quit)
    width = 700
    height = 450
    window.resize(width, height)

    flies = FliesWidget(30, width, height)
    window.add(flies)

    flies.show()
    window.present()
    gtk.main()
