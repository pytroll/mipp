#
# $Id$
#
# Stolen from EUMETSAT's msg_navigation.c
#
# You probaly don't wanna call this one for each point in a full disc image.
#
import math

__all__ = ['GeosNavigation',
           'xy2latlon',
           'latlon2xy',
           'NavigationError']

class NavigationOutside(Exception):
    pass

RAD2DEG = 180./math.pi
DEG2RAD = math.pi/180.

RPOL = 6356.5838
REQ = 6378.1690
H = 42164.0

#-----------------------------------------------------------------------------

class GeosNavigation(object):
    class _Navcoef:
        def __init__(self, sublon, cfac, lfac, coff, loff):
            self.sublon = sublon
            self.cfac = cfac
            self.lfac = lfac
            self.coff = coff
            self.loff = loff
            
    def __init__(self, sublon, cfac, lfac, coff, loff):
        self.navcoef = GeosNavigation._Navcoef(sublon, cfac, lfac, coff, loff)
        
    def lonlat(self, xy, intermediate=False):
        return xy2lonlat(xy, self.navcoef, intermediate)
    
    def xy(self, lonlat, intermediate=False):
        return lonlat2xy(lonlat, self.navcoef, intermediate)

#-----------------------------------------------------------------------------

def xy2lonlat (xy, nav, intermediate=False):

    # Auxiliary variable
    rpol2 = RPOL*RPOL
    req2 = REQ*REQ
    aux1 = 1737121856.0
        
    # Intermediate coordinates
    if intermediate:
        # from km to scan angles
        x = float(xy[0])*math.atan(REQ/H)/REQ
        y = -float(xy[1])*math.atan(RPOL/H)/RPOL
    else:    
        # from column, line to scan angles
        x = ((float(xy[0]) - nav.coff)*pow(2,16)/nav.cfac)*DEG2RAD
        y = ((float(xy[1]) - nav.loff)*pow(2,16)/nav.lfac)*DEG2RAD

    # Auxiliary values 
    cosx = math.cos(x)
    cosy = math.cos(y)
    sinx = math.sin(x)
    siny = math.sin(y)

    aux2 = H*cosx*cosy
    aux3 = cosy*cosy + req2/rpol2*siny*siny
    aux4 = aux2*aux2 - aux3*aux1
    if aux4 < 0:
        raise NavigationOutside("xy2lonlat: point outside earth disk")
        
    sd = math.sqrt(aux4)
    sn = (aux2 - sd)/aux3
    s1 = H - sn*cosx*cosy
    s2 = sn*sinx*cosy
    s3 = -sn*siny
    sxy = math.sqrt(s1*s1 + s2*s2)

    # Longitude and latitude calculation
    lon = RAD2DEG*math.atan(s2/s1) + nav.sublon
    lat = (math.atan(req2/rpol2*s3/sxy))*RAD2DEG

    # Valid range for longitudes [-180,180]
    if lon > 180:
        lon -= 360
    if lon < -180:
        lon += 360

    return lon, lat

def lonlat2xy(lonlat, nav, intermediate=False):
    
    # Auxiliary variable
    rpol2 = RPOL*RPOL
    req2 = REQ*REQ
    aux1 = rpol2/req2
    aux2 = (req2 - rpol2)/req2
    cd = H*H - req2    
    
    # From degrees to radians 
    lon = lonlat[0]*DEG2RAD
    lat = lonlat[1]*DEG2RAD
    sublon = nav.sublon*DEG2RAD

    # Calculte as described in LRIT/HRIT Global Specification section 4.4.3.2
    c_lat = math.atan(aux1*math.tan(lat))
    cosc_lat = math.cos(c_lat)
    rl = RPOL/math.sqrt(1 - aux2*cosc_lat*cosc_lat)
    r1 = H - rl*cosc_lat*math.cos(lon - sublon)
    r2 = -rl*cosc_lat*math.sin(lon - sublon)
    r3 = rl*math.sin(c_lat)
    rn = math.sqrt(r1*r1 + r2*r2 + r3*r3)

    # Compute variables useful to check if pixel is visible from the satellite 
    ad2 = r1*r1 + r2*r2 + r3*r3*req2/rpol2
    bd = H*r1
    delta2 = bd*bd - ad2*cd
    halfsom = bd*rn/ad2
 
    if (delta2 < 0.) or (rn > halfsom):
        raise NavigationOutside("lonlat2xy: coordinates can not be seen from the satellite")
    
    # Intermediate coordinates
    x = math.atan(-r2/r1)
    y = math.asin(-r3/rn)
    
    if intermediate:
        # from scan angles to km
        x = REQ*x/math.atan(REQ/H)
        y = -RPOL*y/math.atan(RPOL/H)
        return x, y

    x *= RAD2DEG
    y *= RAD2DEG
    x = int(round((x*nav.cfac)/pow(2,16) + nav.coff))
    y = int(round((y*nav.lfac)/pow(2,16) + nav.loff))    
    return x, y

#-----------------------------------------------------------------------------

if __name__ == '__main__':
    nav = GeosNavigation(-75.0, 10216334, 10216334, 1408, 1408)
    print nav.lonlat((1408, 1408))
    print nav.xy((-75, 0))
    print nav.lonlat((1408, 60))
    print nav.xy(nav.lonlat((1408, 60)))
    print nav.xy((0,0))