======================
 Calibration comments
======================

MSG series
==========


The calibration of the meteosat second generation satellites is done according to the Eumetsat documents [refl]_, [bt]_.

Reflectances
------------

The visible and near infrared channels are calibrated according to the following formula:

r = R / I

where 
 * r is the bidirectional reflectance factor
 * R is the measured radiance
 * I is the solar irradiance

R is derived from the xRIT data, and I is given in [refl]_.

In [refl]_ the additional following corrections are applied:
 * sun-earth distance correction
 * cosine of the solar zenith angle.

 .. [refl] "Conversion from radiances to reflectances for SEVIRI warm channels"
    EUM/MET/TEN/12/0332
 .. [bt] "The Conversion from Effective Radiances to Equivalent Brightness Temperatures" EUM/MET/TEN/11/0569
