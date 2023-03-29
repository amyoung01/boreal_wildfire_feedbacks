"""
This set of functions performs the CFFDRS calculations described in
Van Wagner 1985 and 1987 for numpy arrays.

Variable names were kept the same as in the original functions.
Furthermore, in this set of functions Equation numbers also directly
match up to those described in the original Fortran code. We also used
'cffdrs' R package to help guide the creation and use of this script.

References:
Van Wagner, C.E. and T. L. Pickett. Equations and FORTRAN program for
the Canadian Forest Fire Weather Index System. 1985. Canadian Forestry
Service, Petawawa National Forestry Institute, Chalk River, Ontario.
Forestry Technical Report 33. 18 p.

Van Wagner, C.E. Development and structure of the Canadian Forest Fire
Weather Index System. 1987. Canadian Forestry Service, Headquarters,
Ottawa. Forestry Technical Report 35. 35 p.

Wang, X. et al. “cffdrs: An R package for the Canadian Forest Fire 
DangerRating System.” Ecological Processes, 6(1), 5. 
https://ecologicalprocesses.springeropen.com/articles/10.1186/s13717-017-0070-z

"""

import numpy as np
import warnings

warnings.filterwarnings('ignore')

# ----------------------------------------------------------------------------
# Fine Fuel Moisture Code
# ----------------------------------------------------------------------------
def ffmc_calc(tas, pr, sfcWind, hurs, ffmc0: np.ndarray=85.0) -> np.ndarray:

    """
    Description
    -----------
    Computes Fine Fuel Moisture Code (FFMC) from the Canadian Forest Fire 
    Danger Rating System (CFFDFRS).

    Parameters
    ----------
    tas: float or numpy.ndarray
        Near-surface (i.e. 2-m) air temperature in degrees Celsius
    pr: float or numpy.ndarray
        Total daily precipitation in mm/day
    sfcWind: float or numpy.ndarray
        10-m wind speed in km/hour
    hurs: float or numpy.ndarray
        Near-surface relative humidity in percent (%). Bound between 0-100
    ffmc0: float or numpy.ndarray, optional
        Fine Fuel Moisture Code for previous day. If not given assumed to be 
        85.0 for first day, and the rest of the calculations proceed through
        time using the previous days ffmc values as they are calculated

    Returns
    -------
    numpy.ndarray
        A numpy.ndarray with fine fuel moisture code output
    """    

    ro = np.copy(pr) # Copy precip data into new numpy array

    mo = 147.2 * (101.0-ffmc0) / (59.5+ffmc0) # ......................... Eq. 1
    
    rf = np.copy(ro)
    rf[ro > 0.5] = rf[ro > 0.5] - 0.5 # ................................. Eq. 2

    mr = np.copy(mo)
    mr = np.where(
        (ro > 0.5) & (mo <= 150.0),
        mo + 42.5 * rf * (np.exp(-100.0/(251.0-mo)))
        * (1.0-np.exp(-6.93/rf)), # .................................... Eq. 3a
        mr)
    mr = np.where(
        (ro > 0.5) & (mo > 150.0),
        mo + 42.5 * rf * (np.exp(-100.0/(251.0-mo)))
        * (1.0 - np.exp(-6.93/rf))
        + 0.0015 * (mo-150.0)**2.0 * np.sqrt(rf), # .................... Eq. 3b
        mr)
    
    mr[mr > 250.0] = 250.0 # mr can't be greater than 250
    
    Ed = 0.942 * hurs**0.679 + 11.0*np.exp((hurs-100.0)/10.0) \
         + 0.18 * (21.1-tas) * (1.0 - 1.0/np.exp(hurs*0.115)) # ......... Eq. 4   
    Ew = 0.618 * hurs**0.753 + 10.0*np.exp((hurs-100.0)/10.0) \
         + 0.18 * (21.1-tas) * (1.0 - 1.0/np.exp(hurs*0.115)) # ......... Eq. 5

    ko = 0.424 * (1.0 - (hurs/100.0)**1.7) \
         + 0.0694 * np.sqrt(sfcWind) * (1.0 - (hurs/100.0)**8.0) # ..... Eq. 6a
    kd = ko * 0.581 * np.exp(0.0365*tas) # ............................. Eq. 6b

    k1 = 0.424*(1.0 - ((100.0-hurs) / 100.0)**1.7) + 0.0694 \
         * np.sqrt(sfcWind) * (1.0 - ((100.0-hurs) / 100.0)**8) #....... Eq. 7a
    kw = k1 * 0.581 * np.exp(0.0365*tas) # ............................. Eq. 7b

    m = np.copy(mr)
    m = np.where(mr > Ed,Ed + (mr-Ed) * 10**-kd,m) # .................... Eq. 8
    m = np.where(mr < Ew,Ew - (Ew-mr) * 10**-kw,m) # .................... Eq. 9

    ffmc = 59.5 * (250.0-m) / (147.2+m) # .............................. Eq. 10

    # Constrain ffmc values to a max of 101.0. Could be theoretically higher 
    # than this when moisture content (m) is less than 0.05.
    ffmc = np.where(ffmc > 101.0,101.0,ffmc)

    return ffmc[...]

# ----------------------------------------------------------------------------
# Duff Moisture Code
# ----------------------------------------------------------------------------
def dmc_calc(tas, pr, hurs, mon, dmc0: np.ndarray=6.0) -> np.ndarray:

    """
    Description
    -----------
    Computes Duff Moisture Code (DMC) from the Canadian Forest Fire 
    Danger Rating System (CFFDFRS).

    Parameters
    ----------
    tas: float or numpy.ndarray
        Near-surface (i.e. 2-m) air temperature in degrees Celsius
    pr: float or numpy.ndarray
        Total daily precipitation in mm/day
    hurs: float or numpy.ndarray
        Near-surface relative humidity in percent (%). Bound between 0-100
    dmc0: float or numpy.ndarray, optional
        Duff moisture for previous day. If not given assumed to be 
        6.0 for first day, and the rest of the calculations proceed through
        time using the previous days dmc values as they are calculated

    Returns
    -------
    numpy.ndarray
        A numpy.ndarray with fine duff moisture code output
    """      

    # Initialize parameters
    ro = np.copy(pr) # Re-name pr as ro
    Po = np.copy(dmc0) # Re-name previous days DMC as Po
    tas = np.where(tas < -1.1,-1.1,tas) # tas values can't be < -1.1

    # Parameters for effective daylight hours
    Le = np.array([
        6.5, 7.5, 9.0, 12.8, 13.9, 13.9, 12.4, 10.9, 9.4, 8.0, 7.0, 6.0])

    re = np.where(ro > 1.5,0.92*ro - 1.27,ro) # ........................ Eq. 11
    Mo = 20.0 + np.exp(5.6348 - Po/43.43) # ............................ Eq. 12

    b = 100.0 / (0.5 + 0.3*Po) # ...................................... Eq. 13a
    b = np.where((Po > 33.0) & (Po <= 65.0),14 - 1.3*np.log(Po),b) #..  Eq. 13b
    b = np.where(Po > 65.0,6.2*np.log(Po) - 17.2,b) # ................. Eq. 13c          

    Mr = np.where(ro > 1.5,Mo + 1000.0 * re/(48.77 + b*re),0.0) # ...... Eq. 14
    Pr = np.where(ro > 1.5,244.72 - 43.43 * np.log(Mr-20.0),Po) # ...... Eq. 15
    
    Pr[Pr < 0.0] = 0.0
        
    K = 1.894 * (tas+1.1) * (100.0-hurs) * Le[mon]*1e-06 # ............. Eq. 16

    dmc = Pr + 100.0*K # ............................................... Eq. 17

    return dmc[...]

# ----------------------------------------------------------------------------
# Drought Code
# ----------------------------------------------------------------------------
def dc_calc(tas, pr, mon, dc0: np.ndarray=15.0) -> np.ndarray:

    """
    Description
    -----------
    Computes Drought Code (DMC) from the Canadian Forest Fire 
    Danger Rating System (CFFDFRS).

    Parameters
    ----------
    tas: float or numpy.ndarray
        Near-surface (i.e. 2-m) air temperature in degrees Celsius
    pr: float or numpy.ndarray
        Total daily precipitation in mm/day
    dc0: float or numpy.ndarray, optional
        Drought for previous day. If not given assumed to be 
        15.0 for first day, and the rest of the calculations proceed through
        time using the previous days dc values as they are calculated

    Returns
    -------
    numpy.ndarray
        A numpy.ndarray with fine drought code output
    """       

    ro = np.copy(pr)
    Do = np.copy(dc0)

    tas[tas < -2.8] = -2.8

    Lf = np.array([-1.6,-1.6,-1.6,0.9,3.8,5.8,6.4,5.0,2.4,0.4,-1.6,-1.6])

    rd = np.where(ro > 2.8,0.83*ro - 1.27,0.0) # ....................... Eq. 18

    Qo = 800.0 * np.exp(-1 * Do/400.0) # ............................... Eq. 19
    Qr = Qo + 3.937*rd # ............................................... Eq. 20
    Dr = 400.0 * np.log(800.0/Qr) # .................................... Eq. 21
    
    Dr = np.where(ro <= 2.8,Do,Dr)
    Dr[Dr < 0.0] = 0.0

    V = 0.36 * (tas+2.8) + Lf[mon] # ................................... Eq. 22
    V = np.where(V < 0.0,0.0,V)
    
    dc = Dr + V/2 # .................................................... Eq. 23
    
    return dc[...]

# -----------------------------------------------------------------------------
# Initial Spread Index
# -----------------------------------------------------------------------------
def isi_calc(ffmc, sfcWind) -> np.ndarray:

    """
    Description
    -----------
    Computes Initial Spread Index from the Canadian Forest Fire 
    Danger Rating System (CFFDFRS).

    Parameters
    ----------
    ffmc: float or numpy.ndarray
        Current day's Fine Fuel Moisture Code
    sfcWind: float or numpy.ndarray
        10-m wind speed in km/hour

    Returns
    -------
    numpy.ndarray
        A numpy.ndarray with initial spread index output
    """       

    m = 147.2 * (101.0-ffmc)/(59.5+ffmc) # .............................. Eq. 1
                                         # (See Van Wagner 1987 p. 20)

    fW = np.exp(0.05039*sfcWind) # ..................................... Eq. 24
    fF = 91.9 * np.exp(-0.1386*m) \
         * (1.0 + (m**5.31)/(4.93*1e7)) # .............................. Eq. 25

    isi = 0.208*fW*fF #................................................. Eq. 26

    return isi[...]

# -----------------------------------------------------------------------------
# Build Up Index
# -----------------------------------------------------------------------------
def bui_calc(dmc, dc) -> np.ndarray:

    """
    Description
    -----------
    Computes Build Up Index from the Canadian Forest Fire 
    Danger Rating System (CFFDFRS).

    Parameters
    ----------
    dmc: float or numpy.ndarray
        Current day's duff moisture code
    dc: float or numpy.ndarray
        Current day's drought code

    Returns
    -------
    numpy.ndarray
        A numpy.ndarray with build-up index output
    """     

    P = np.copy(dmc)
    D = np.copy(dc)

    P[P < 0.001] = 0.0

    bui = np.where(P <= 0.4 * D,
            0.8 * P * D/(P + 0.4*D), # ................................ Eq. 27a
            P - (1.0 - 0.8*D/(P + 0.4*D)) \
            * (0.92 + (0.0114*P)**1.7)) # ............................. Eq. 27b

    bui = np.where((P == 0.0) & (D == 0.0),0.0,bui)
    bui = np.where(bui < 0.0,0.0,bui)

    return bui[...]

# -----------------------------------------------------------------------------
# Fire Weather Index
# -----------------------------------------------------------------------------
def fwi_calc(isi, bui) -> np.ndarray:

    """
    Description
    -----------
    Computes Fire Weather Index from the Canadian Forest Fire 
    Danger Rating System (CFFDFRS).

    Parameters
    ----------
    isi: float or numpy.ndarray
        Current day's initial spread index
    bui: float or numpy.ndarray
        Current day's build up index

    Returns
    -------
    numpy.ndarray
        A numpy.ndarray with fire weather index output
    """     

    R = np.copy(isi)
    U = np.copy(bui)

    fD = np.where(U <= 80.0,
            0.626 * U**0.809 + 2.0, # ................................. Eq. 28a
            1000.0/(25.0 + 108.64*np.exp(-0.0203*U))) # ............... Eq. 28b

    B = 0.1 * R * fD # ................................................. Eq. 29

    fwi = np.where(B > 1.0,
            np.exp(2.72 * (0.434*np.log(B))**0.647), # ................ Eq. 30a
            B) # ...................................................... Eq. 30b

    return fwi[...]

# -----------------------------------------------------------------------------
# Daily Severity Rating
# -----------------------------------------------------------------------------
def dsr_calc(fwi) -> np.ndarray:

    """
    Description
    -----------
    Computes Daily Severity Rating from the Canadian Forest Fire 
    Danger Rating System (CFFDFRS).

    Parameters
    ----------
    fwi: float or numpy.ndarray
        Current day's fire weather index

    Returns
    -------
    numpy.ndarray
        A numpy.ndarray with daily severity rating output
    """         

    dsr = 0.0272 * fwi**1.77 # ......................................... Eq. 31

    return dsr[...]

def cffdrs_calc(
        tas: np.ndarray,
        pr: np.ndarray,
        sfcWind: np.ndarray,
        hurs: np.ndarray,
        mon,
        ffmc0: np.ndarray=85.0,
        dmc0: np.ndarray=6.0,
        dc0: np.ndarray=15.0
        ) -> dict:

    """
    Description
    -----------
    Computes CFFDRS Indices using near-surface air temperature (tas,[degC]), 
    total precipitation (pr,[mm/day]), 10-metre wind speed (sfcWind,[km/hour]), 
    and near-surface relative humidity (hurs,[%]).

    Parameters
    ----------
    tas: float or numpy.ndarray
        Near-surface (i.e. 2-m) air temperature in degrees Celsius
    pr: float or numpy.ndarray
        Total daily precipitation in mm/day
    sfcWind: float or numpy.ndarray
        10-m wind speed in km/hour
    hurs: float or numpy.ndarray
        Near-surface relative humidity in percent (%). Bound between 0-100
    mon: int or numpy.ndarray(dtype=int)
        Month values (1-12) for each day of year included in input array.
    ffmc0: float or numpy.ndarray, optional
        Fine Fuel Moisture Code for previous day. If not given assumed to be 
        85.0 for first day, and the rest of the calculations proceed through
        time using the previous days ffmc values as they are calculated
    dmc0: float or numpy.ndarray, optional
        Duff Moisture Code for previous day. If not given assumed to be 
        6.0 for first day, and the rest of the calculations proceed through
        time using the previous days ffmc values as they are calculated
    dc0: float or numpy.ndarray, optional
        Drought Code for previous day. If not given assumed to be 
        15.0 for first day, and the rest of the calculations proceed through
        time using the previous days ffmc values as they are calculated

    Returns
    -------
    dict
        A dictionary with the following keys:
            ffmc: float or numpy array of floats
                Fine fuel moisture code
            dmc: float or numpy array of floats
                Duff moisture code
            dc: float or numpy array of floats
                Drought code
            isi: float or numpy array of floats
                Initial spread index [unitless]
            bui: float or numpy array of floats
                Build-up index [unitless]
            fwi: float or numpy array of floats
                Fire weather index [unitless]
            dsr: float or numpy array of floats
                Daily severity rating [unitless]
    
    Notes
    -----
    The first axis of any supplied numpy.ndarray is the time axis. For 
    example, in 3D arrays this means that axis 0 represent time and axes 1 and 
    2 represent the spatial dimensions (e.g., lat and lon).
    """

    # Create empty arrays to store cffdrs variables
    arr_shape = tas.shape

    ffmc = np.zeros(arr_shape)
    dmc = np.zeros(arr_shape)
    dc = np.zeros(arr_shape)
    isi = np.zeros(arr_shape)
    bui = np.zeros(arr_shape)
    fwi = np.zeros(arr_shape)
    dsr = np.zeros(arr_shape)

    ndays = mon.size

    for i in range(ndays):

        ffmc[i,...] = ffmc_calc(
            tas[i,...],pr[i,...],sfcWind[i,...],hurs[i,...],ffmc0)
        dmc[i,...] = dmc_calc(
            tas[i,...],pr[i,...],hurs[i,...],mon[i]-1,dmc0)
        dc[i,...] = dc_calc(
            tas[i,...],pr[i,...],mon[i]-1,dc0)
        isi[i,...] = isi_calc(
            ffmc[i,...],sfcWind[i,...])
        bui[i,...] = bui_calc(
            dmc[i,...],dc[i,...])
        fwi[i,...] = fwi_calc(
            isi[i,...],bui[i,...])
        dsr[i,...] = dsr_calc(
            fwi[i,...])

        ffmc0 = ffmc[i,...]
        dmc0 = dmc[i,...]
        dc0 = dc[i,...]

    return {
        'ffmc': ffmc,
        'dmc': dmc,
        'dc': dc,
        'isi': isi,
        'bui': bui,
        'fwi': fwi,
        'dsr': dsr,
        }