import gi, cairo, math
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk, Gdk, GdkPixbuf
import threading
import socket
import select
import sys
    
class NetworkOutgoing(threading.Thread):
    def __init__(self):
        threading.Thread.__init__(self)
        self.HOST = ""
        self.PORT = 1338
        self.running = 1
        self.daemon = True

    def run(self):
        self.p2p_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.p2p_socket.bind((self.HOST,self.PORT))
        self.p2p_socket.listen(1)
        self.conn, self.addr = self.p2p_socket.accept()

        while self.running == True:
            print("General Kenobi")
            
            inputready,outputready,exceptready \
            = select.select ([self.conn],[self.conn],[])
            for input_item in inputready:
                # Handle sockets
                message = self.conn.recv(1024)

    def kill(self):
        self.running = 0

class NetworkIncoming(threading.Thread):
    def __init__(self):
        threading.Thread.__init__(self)
        self.HOST = "127.0.0.1"
        self.PORT = 1338
        self.running = 1
        self.daemon = True
    
    def run(self):
        self.p2p_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.p2p_socket.connect((self.HOST, self.PORT))
        
        while self.running == True:
            print("Hello There")
            
            inputready,outputready,exceptready \
            = select.select ([self.conn],[self.conn],[])
            for input_item in inputready:
                # Handle sockets
                message = self.conn.recv(1024)
    
    def kill(self):
        self.running = 0

class StratCaller(Gtk.Window):
    def changeMap(self, maptochange):
        print("Hello, map changed to " + maptochange.props.label)
        self.map = maptochange.props.label
        Gtk.Widget.queue_draw(self.drawingarea)

    def draw(self, da, ctx):
        #print("Drawing " + self.map)
        image = cairo.ImageSurface.create_from_png ("Maps/" + self.map + ".png")
        
        imageheight = float(image.get_width())
        imagewidth = float(image.get_height())
        width = float(self.window.get_size().width) - 40
        height = float(self.window.get_size().height) - 40

        scale = min(width/imagewidth, height/imageheight)
        
        self.x2 = self.x1 + imagewidth*scale
        self.y2 = self.y1 + imageheight*scale

        self.context = ctx
        self.context.scale(scale, scale)
        self.context.set_source_surface(image, 20, 20)
        self.context.paint()
        
        self.context.scale(1/scale, 1/scale)
        
        
        self.context.set_source_rgb(0.0, 0.0, 0.8)
        
        for points in self.clicks:
            for point in points:
                if isinstance(point, list):
                    if point[2] != self.context.get_line_width():
                            self.context.stroke()
                            self.context.set_line_width(point[2])
                    self.context.line_to(point[0], point[1])
                elif points[0] < 0:
                    self.context.stroke()
                else:
                    if points[2] != self.context.get_line_width():
                        self.context.stroke()
                        self.context.set_line_width(points[2])
                    self.context.set_line_width(points[2])
                    self.context.line_to(points[0], points[1])
                    
        self.context.stroke()

    def drawLine(self, da, event):
        if (float(event.x) > float(self.x1)) & (float(event.y) > float(self.y1)) & (float(event.x) < float(self.x2)) & (float(event.y) < float(self.y2)):
            if event.button == 1:
                self.clicks.append([event.x, event.y, self.lineWidth])
            elif event.button == 3:
                self.clicks.append([-1, -1])

            Gtk.Widget.queue_draw(self.drawingarea)

    def drawLineDrag(self, da, event):
        if (float(event.x) > float(self.x1)) & (float(event.y) > float(self.y1)) & (float(event.x) < float(self.x2)) & (float(event.y) < float(self.y2)):
            self.clicks[len(self.clicks)-1].append([event.x, event.y, self.lineWidth])
        
            Gtk.Widget.queue_draw(self.drawingarea)

    def undoAction(self, object):
        self.clicks.pop()
        Gtk.Widget.queue_draw(self.drawingarea)

    def add_resized_icons(self):    
        for x in range(1,6):
            print("Connecting icons")
            pixbuf = GdkPixbuf.Pixbuf.new_from_file_at_size("Icons/" + str(x) + ".png", 50, 50)
            self.builder.get_object(str(x) + "icon").set_from_pixbuf(pixbuf)

    def changeLineWidth(self, spinButton):
        self.lineWidth = spinButton.get_value()
        Gtk.Widget.queue_draw(self.drawingarea)
    
    def do_delete_event(self, object, event):
        print("Closing")
        self.Network_Outgoing.kill()
        self.Network_Incoming.kill()
        Gtk.main_quit
        sys.exit()

    def __init__(self):
        self.Network_Outgoing = NetworkOutgoing()
        self.Network_Incoming = NetworkIncoming()

        self.Network_Outgoing.start()
        self.Network_Incoming.start()

        self.map = "Cache"
        self.lineWidth = 1
        self.clicks = []
        self.last_point = [0, 0]

        self.x1 = 20
        self.y1 = 20

        self.builder = Gtk.Builder()
        self.builder.add_from_file("gui.glade")
        self.window = self.builder.get_object("mainwindow")
        self.window.connect("delete-event", self.do_delete_event)
        
        self.window.maximize()

        handlers = {
                "changeMap": self.changeMap,
                "undoAction" : self.undoAction,
                "changeLineWidth": self.changeLineWidth
            }
        self.builder.connect_signals(handlers)

        self.drawingarea = Gtk.DrawingArea(hexpand = True, vexpand = True, can_focus=True)
        
        #Add events
        self.drawingarea.add_events(Gdk.EventMask.BUTTON_PRESS_MASK)
        self.drawingarea.add_events(Gdk.EventMask.BUTTON_MOTION_MASK)
        
        #Connect Events
        self.drawingarea.connect("motion-notify-event", self.drawLineDrag)
        self.drawingarea.connect("button-press-event", self.drawLine)
        self.drawingarea.connect("draw", self.draw)
        
        self.builder.get_object("maingrid").attach(self.drawingarea, 0, 0, 40, 40)
        
        self.add_resized_icons()

        #print(dir(window.props))

        self.window.show_all()
    

if __name__ == "__main__":
    StratCaller()
    Gtk.main()