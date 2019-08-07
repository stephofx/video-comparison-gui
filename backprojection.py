import math
import numpy as np

tilt_angle = math.pi/4

sensor_width, sensor_height = (4.8, 3.6) # 1/3" in mm
focal_length = 3.6

h_fov = 2*math.atan2(sensor_width,(2*focal_length))
v_fov = 2*math.atan2(sensor_height,(2*focal_length))

r_x = 600 # Resolution in width (px)
r_y = 800 # Resolution in height (px)

camera_height = 545 # height of camera center to ground (mm)
#camera_height = 1625
pot_height = 369 # height from ground to top of pot
soil_height = 333 # height from ground to top of soil

"""
alpha_beta:
    Calculate alpha and beta given the projected x and projected y coordinates
    (x_p, y_p), which will be used to rotate a vector to find the projected
    line through the target point, l_p.
"""

def alpha_beta(x_p, y_p):
    beta = (-x_p/r_x)*h_fov
    alpha = (-y_p/r_y)*v_fov + tilt_angle
    return alpha, beta

"""
lp_projection_calibration:
    finds the vector r in the direction of the projected line l_p for the given
    point, which is assumed to be at the top of the soil for calibration.
    r_f = (a, b, c). l_p is of the form:
        x = x_0 + a*t
        y = y_0 + b*t
        z = z_0 + c*t
    Returns t.
"""

def lp_projection_calibration(alpha, beta):
    r_s = np.array([0, 1, 0])
    rot_x = np.array([[1, 0, 0],
                     [0, np.cos(alpha), -np.sin(alpha)],
                     [0, np.sin(alpha), np.cos(alpha)]])
    rot_z = np.array([[np.cos(beta), -np.sin(beta), 0],
                     [np.sin(beta), np.cos(beta), 0],
                     [0, 0, 1]])
    r_f = np.matmul(np.matmul(rot_x, rot_z), r_s)

    # Solve for parametric t for l_p

    t = (soil_height - camera_height)/r_f[2]
    # t = (0 - camera_height)/r_f[2] # change 0 back to soil height FIXME
    return t

"""
lp_projection:
    finds the vector r in the direction of the projected line l_p for the given
    point, where t is assumed to be found.
    r_f = (a, b, c). l_p is of the form:
        x = x_0 + a*t
        y = y_0 + b*t
        z = z_0 + c*t
    Returns height of given point.
"""

def lp_projection(alpha, beta, t):
    r_s = np.array([0, 1, 0])
    rot_x = np.array([[1, 0, 0],
                     [0, np.cos(alpha), -np.sin(alpha)],
                     [0, np.sin(alpha), np.cos(alpha)]])
    rot_z = np.array([[np.cos(beta), -np.sin(beta), 0],
                     [np.sin(beta), np.cos(beta), 0],
                     [0, 0, 1]])
    r_f = np.matmul(np.matmul(rot_x, rot_z), r_s)

    z = camera_height + r_f[2]*t
    return math.fabs(soil_height-z)/25.4
    #return z/25.4

