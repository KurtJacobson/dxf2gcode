#!/usr/bin/python
# -*- coding: cp1252 -*-
#
#dxf2gcode_b02_shape.py
#Programmers:   Christian Kohl�ffel
#               Vinzenz Schulz
#
#Distributed under the terms of the GPL (GNU Public License)
#
#dxf2gcode is free software; you can redistribute it and/or modify
#it under the terms of the GNU General Public License as published by
#the Free Software Foundation; either version 2 of the License, or
#(at your option) any later version.
#
#This program is distributed in the hope that it will be useful,
#but WITHOUT ANY WARRANTY; without even the implied warranty of
#MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#GNU General Public License for more details.
#
#You should have received a copy of the GNU General Public License
#along with this program; if not, write to the Free Software
#Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA  02111-1307  USA
#
#Main Class Shape

#import sys, os, string, ConfigParser 
from dxf2gcode_b02_point import PointClass, LineGeo, ArcGeo
from math import cos, sin, radians, degrees
import wx
from wx.lib.expando import ExpandoTextCtrl

class ShapeClass:
    def __init__(self,nr='None',closed=0,
                cut_cor=40,length=0.0,
                parent=None,
                geos=[],geos_hdls=[]):
                    
        self.type="Shape"
        self.nr=nr
        self.closed=closed
        self.cut_cor=40
        self.length=length
        self.parent=parent
        self.geos=geos
        self.geos_hdls=geos_hdls

    def __str__(self):
        return ('\ntype:        %s' %self.type)+\
               ('\nnr:          %i' %self.nr)+\
               ('\nclosed:      %i' %self.closed)+\
               ('\ncut_cor:     %s' %self.cut_cor)+\
               ('\nlen(geos):   %i' %len(self.geos))+\
               ('\nlength:      %0.2f' %self.length)+\
               ('\ngeos:        %s' %self.geos)+\
               ('\ngeos_hdls:   %s' %self.geos_hdls)
               #+\
               #('\nparent: %s' %self.parent)

    def reverse(self):
        self.geos.reverse()
        for geo in self.geos: 
            geo.reverse()

    def switch_cut_cor(self):
        if self.cut_cor==41:
            self.cut_cor=42
        elif self.cut_cor==42:
            self.cut_cor=41

    def get_st_en_points(self):
        st_point, st_angle=self.geos[0].get_start_end_points(0)
        start=st_point.rot_sca_abs(self.EntitieContent)
        
        en_point, en_angle=self.geos[-1].get_start_end_points(1)
        ende=en_point.rot_sca_abs(self.EntitieContent)
        return [start,ende]

    def plot2can(self,Canvas=None,tag=None,col='Black'):
        
        for i in range(len(self.geos)):
            cur_pts=self.geos[i].plot2can(self.parent)

            if i==0:
                points=cur_pts
            else:
                points+=cur_pts[1:len(cur_pts)]
                       
        self.geo_hdl=Canvas.AddLine(points, LineWidth = 2, LineColor = col)
        

        
    def plot_cut_info(self,Canvas,config,length):
        hdls=[]
        hdls.append(self.plot_start(Canvas,length))
        hdls.append(self.plot_end(Canvas,length))
        if self.cut_cor>40:
            hdls.append(self.plot_cut_cor(Canvas,length))
               
            self.make_start_moves(config)
            #hdls+=self.st_move[1].plot2can(CanvasClass.canvas,P0,sca,tag=self.nr,col='SteelBlue3')
            #hdls+=self.st_move[2].plot2can(CanvasClass.canvas,P0,sca,tag=self.nr,col='SteelBlue3')
        return hdls
            
    def plot_start(self,Canvas=None,length=20):
        st_point, st_angle=self.geos[0].get_start_end_points(0)
                
        start=st_point.rot_sca_abs(parent=self.parent)
        
        dx=cos(radians(st_angle))*length
        dy=sin(radians(st_angle))*length

        hdl=Canvas.AddArrowLine([[start.x,start.y],[start.x+dx,start.y+dy]],
                                LineWidth=2, 
                                LineColor= "BLUE",
                                ArrowHeadSize = 18,
                                ArrowHeadAngle = 18)
        return hdl
    
    

    def plot_cut_cor(self,Canvas=None,length=20):
        st_point, st_angle=self.geos[0].get_start_end_points(0)
        start=st_point.rot_sca_abs(parent=self.parent)

        if self.cut_cor==41:
            st_angle=st_angle+90
        else:
            st_angle=st_angle-90
            
        dx=cos(radians(st_angle))*length
        dy=sin(radians(st_angle))*length

        hdl=Canvas.AddArrowLine([[start.x,start.y],[start.x+dx,start.y+dy]],
                                LineWidth=2,
                                LineColor= "BLUE",
                                ArrowHeadSize = 18,
                                ArrowHeadAngle = 18)
        return hdl

    def plot_end(self,Canvas=None,length=20):
        en_point, en_angle=self.geos[-1].get_start_end_points(1)
           
        ende=en_point.rot_sca_abs(parent=self.parent)
        
        dx=cos(radians(en_angle))*length
        dy=sin(radians(en_angle))*length

        hdl=Canvas.AddArrowLine([[ende.x+dx,ende.y+dy],[ende.x,ende.y]],
                                LineWidth=2,
                                LineColor= "GREEN",
                                ArrowHeadSize = 18,
                                ArrowHeadAngle = 18)
        return hdl

    def make_start_moves(self,config):
        self.st_move=[]

        #Einlaufradius und Versatz 
        start_rad=config.start_rad
        start_ver=start_rad

        #Werkzeugdurchmesser in Radius umrechnen        
        tool_rad=config.tool_dia/2
    
        #Errechnen des Startpunkts mit und ohne Werkzeug Kompensation        
        sp, sa=self.geos[0].get_start_end_points(0)
        start_cont=(sp*self.parent.sca)+self.parent.p0
      
        if self.cut_cor==40:              
            self.st_move.append(start_cont)

        #Fr�sradiuskorrektur Links        
        elif self.cut_cor==41:
            #Mittelpunkts f�r Einlaufradius
            Oein=start_cont.get_arc_point(sa+90,start_rad+tool_rad)
            #Startpunkts f�r Einlaufradius
            Pa_ein=Oein.get_arc_point(sa+180,start_rad+tool_rad)
            #Startwerts f�r Einlaufgerade
            Pg_ein=Pa_ein.get_arc_point(sa+90,start_ver)
            
            #Eintauchpunkts errechnete Korrektur
            start_ein=Pg_ein.get_arc_point(sa,tool_rad)
            self.st_move.append(start_ein)

            #Einlaufgerade mit Korrektur
            start_line=LineGeo(Pg_ein,Pa_ein)
            self.st_move.append(start_line)

            #Einlaufradius mit Korrektur
            start_rad=ArcGeo(Pa=Pa_ein,Pe=start_cont,O=Oein,r=start_rad+tool_rad,dir=1)
            self.st_move.append(start_rad)
            
        #Fr�sradiuskorrektur Rechts        
        elif self.cut_cor==42:

            #Mittelpunkt f�r Einlaufradius
            Oein=start_cont.get_arc_point(sa-90,start_rad+tool_rad)
            #Startpunkt f�r Einlaufradius
            Pa_ein=Oein.get_arc_point(sa+180,start_rad+tool_rad)
            IJ=Oein-Pa_ein
            #Startwerts f�r Einlaufgerade
            Pg_ein=Pa_ein.get_arc_point(sa-90,start_ver)
            
            #Eintauchpunkts errechnete Korrektur
            start_ein=Pg_ein.get_arc_point(sa,tool_rad)
            self.st_move.append(start_ein)

            #Einlaufgerade mit Korrektur
            start_line=LineGeo(Pg_ein,Pa_ein)
            self.st_move.append(start_line)

            #Einlaufradius mit Korrektur
            start_rad=ArcGeo(Pa=Pa_ein,Pe=start_cont,O=Oein,r=start_rad+tool_rad,dir=0)
            self.st_move.append(start_rad)
    
    def Write_GCode(self,config,postpro):

        #Erneutes erstellen der Einlaufgeometrien
        self.make_start_moves(config)
        
        #Werkzeugdurchmesser in Radius umrechnen        
        tool_rad=config.tool_dia/2
        
        depth=config.axis3_mill_depth
        max_slice=config.axis3_slice_depth

        #Scheibchendicke bei Fr�stiefe auf Fr�stiefe begrenzen
        if -abs(max_slice)<=depth:
            mom_depth=depth
        else:
            mom_depth=-abs(max_slice)


        #Positionieren des Werkzeugs �ber dem Anfang und Eintauchen
        self.st_move[0].Write_GCode([1,1,1],\
                                    PointClass(x=0,y=0),\
                                    PointClass(x=0,y=0),
                                    0.0,\
                                    postpro)
        
        postpro.rap_pos_z(config.axis3_safe_margin)
        postpro.chg_feed_rate(config.F_G1_Depth)
        postpro.lin_pol_z(mom_depth)
        postpro.chg_feed_rate(config.F_G1_Plane)

        #Wenn G41 oder G42 an ist Fr�sradiuskorrektur        
        if self.cut_cor!=40:
            
            #Errechnen des Startpunkts ohne Werkzeug Kompensation
            #und einschalten der Kompensation     
            start_cor, sa=self.st_move[1].get_start_end_points(0)
            postpro.set_cut_cor(self.cut_cor,start_cor)
            
            self.st_move[1].Write_GCode([1,1,1],\
                                    PointClass(x=0,y=0),\
                                    PointClass(x=0,y=0),
                                    0.0,\
                                    postpro)
            
            self.st_move[2].Write_GCode([1,1,1],\
                                    PointClass(x=0,y=0),\
                                    PointClass(x=0,y=0),
                                    0.0,\
                                    postpro)

        #Schreiben der Geometrien f�r den ersten Schnitt
        for geo in self.geos:
            geo.Write_GCode(self.sca,self.p0,self.rot,postpro)

        #Ausschalten der Fr�sradiuskorrektur
        if (not(self.cut_cor==40))&(postpro.cancel_cc_for_depth==1):
            en_point, en_angle=self.geos[-1].get_start_end_points(-1)
            end_cont=(en_point*self.sca)+self.p0
            if self.cut_cor==41:
                pos_cut_out=end_cont.get_arc_point(en_angle-90,tool_rad)
            elif self.cut_cor==42:
                pos_cut_out=end_cont.get_arc_point(en_angle+90,tool_rad)         
            postpro.deactivate_cut_cor(pos_cut_out)            

        #Z�hlen der Schleifen
        snr=0
        #Schleifen f�r die Anzahl der Schnitte
        while mom_depth>depth:
            snr+=1
            mom_depth=mom_depth-abs(max_slice)
            if mom_depth<depth:
                mom_depth=depth                

            #Erneutes Eintauchen
            postpro.chg_feed_rate(config.F_G1_Depth)
            postpro.lin_pol_z(mom_depth)
            postpro.chg_feed_rate(config.F_G1_Plane)

            #Falls es keine geschlossene Kontur ist    
            if self.closed==0:
                self.reverse()
                self.switch_cut_cor()
                
            #Falls cut correction eingeschaltet ist diese einschalten.
            if ((not(self.cut_cor==40))&(self.closed==0))or(postpro.cancel_cc_for_depth==1):
                #Errechnen des Startpunkts ohne Werkzeug Kompensation
                #und einschalten der Kompensation     
                sp, sa=self.geos[0].get_start_end_points(0)
                start_cor=(sp*self.sca)+self.p0
                postpro.set_cut_cor(self.cut_cor,start_cor)
                
            for geo_nr in range(len(self.geos)):
                self.geos[geo_nr].Write_GCode(self.entitie.sca,self.entitie.p0,
                                                self.entitie.pb,
                                                self.entitie.rot,postpro)

            #Errechnen des Konturwerte mit Fr�sradiuskorrektur und ohne
            en_point, en_angle=self.geos[-1].get_start_end_points(-1)
            en_point=(en_point*self.sca)+self.p0
            if self.cut_cor==41:
                en_point=en_point.get_arc_point(en_angle-90,tool_rad)
            elif self.cut_cor==42:
                en_point=en_point.get_arc_point(en_angle+90,tool_rad)

            #Ausschalten der Fr�sradiuskorrektur falls ben�tigt          
            if (not(self.cut_cor==40))&(postpro.cancel_cc_for_depth==1):         
                postpro.deactivate_cut_cor(en_point)
     
        #Anfangswert f�r Direction wieder herstellen falls n�tig
        if (snr%2)>0:
            self.reverse()
            self.switch_cut_cor()

        #Fertig und Zur�ckziehen des Werkzeugs
        postpro.lin_pol_z(config.axis3_safe_margin)
        postpro.rap_pos_z(config.axis3_retract)

        #Falls Fr�sradius Korrektur noch nicht ausgeschaltet ist ausschalten.
        if (not(self.cut_cor==40))&(not(postpro.cancel_cc_for_depth)):
            postpro.deactivate_cut_cor(en_point)        

        return 1    
    
class EntitieContentClass:
    def __init__(self,type="Entitie",Nr=None,Name='',parent=None,children=[],
                p0=PointClass(x=0.0,y=0.0),pb=PointClass(x=0.0,y=0.0),sca=[1,1,1],rot=0.0):
                    
        self.type=type
        self.Nr=Nr
        self.Name=Name
        self.children=children
        self.p0=p0
        self.pb=pb
        self.sca=sca
        self.rot=rot
        self.parent=parent

    def __cmp__(self, other):
         return cmp(self.EntNr, other.EntNr)        
        
    def __str__(self):
        return ('\ntype:        %s' %self.type) +\
               ('\nNr :      %i' %self.Nr) +\
               ('\nName:     %s' %self.Name)+\
               ('\np0:          %s' %self.p0)+\
               ('\npb:          %s' %self.pb)+\
               ('\nsca:         %s' %self.sca)+\
               ('\nrot:         %s' %self.rot)+\
               ('\nchildren:    %s' %self.children)
            
    #Hinzufuegen der Kontur zu den Entities
    def addchild(self,child):
        self.children.append(child)
        
    def MakeTreeText(self,parent):
        #font1 = wx.Font(8,wx.SWISS, wx.NORMAL, wx.NORMAL)
        textctrl = ExpandoTextCtrl(parent, -1, "", 
                            size=wx.Size(160,55))
                            
        
        #textctrl.SetFont(font1)
                                
        #dastyle = wx.TextAttr()
        #dastyle.SetTabs([100, 120])
        #textctrl.SetDefaultStyle(dastyle)
        textctrl.AppendText('Point:  X:%0.2f Y%0.2f\n' %(self.p0.x, self.p0.y))
        textctrl.AppendText('Offset: X:%0.2f Y%0.2f\n' %(self.pb.x, self.pb.y))
        textctrl.AppendText('rot: %0.1fdeg sca: %s' %(degrees(self.rot), self.sca))
        return textctrl