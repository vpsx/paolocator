## Getting a tilt-compensated heading from the LSM303DLHC
**...or any other magnetometer, probably**

At any location, the Earth's magnetic field can be represented by a three-dimensional vector. A typical procedure for measuring its direction is to use a compass to determine the direction of magnetic North. Its angle relative to true North is the declination or variation. Facing magnetic North, the angle the field makes with the horizontal is the inclination or magnetic dip. The intensity of the field is proportional to the force it exerts on a magnet. Another common representation is in X (North), Y (East) and Z (Down) coordinates. (--Wikipedia)

<img src="https://upload.wikimedia.org/wikipedia/commons/1/16/XYZ-DIS_magnetic_field_coordinates.svg" width="800" alt="Common coordinate systems used for representing the Earth's magnetic field."/>

So that's the Earth and its magnetic field. The three magnetometer readings, then, together express this red "magnetic North" vector, relative to the axes on the magnetometer itself.

<details markdown="1">
<summary>In particular, the LSM303DLHC's magnetometer readings are in <a href="https://en.wikipedia.org/wiki/Gauss_(unit)">gauss</a>...</summary>

...and you <a href="https://cdn-shop.adafruit.com/datasheets/LSM303DLHC.PDF">can select</a> sensitivities between +-1.3 and +-8.0 gauss, except I haven't actually figured out how to do that yet. The Earth's magnetic field at its surface ranges from about 0.25–0.60 Gs; a typical refrigerator magnet has a field of about 50 Gs. I'm not sure yet, but probably this is good to know for sanity-checking your raw measurements when debugging magnetometer code...
</details>

If you ignore geographic North and pretend that magnetic North is the One True North, then you can take your magnetometer, define your "head" (nose?) as the positive x-axis, wave your hands, and say that your heading is the angle subtended by the positive x-axis and the vector defined by your readings, projected on to the x-y plane. (Or have the magnetometer level with the ground and ignore the z-axis reading altogether.)

<details markdown="1">
<summary>Or if you don't want to pretend...</summary>
...then you can use the National Oceanic and Atmospheric Administration's <a href="https://www.ngdc.noaa.gov/geomag/calculators/magcalc.shtml"> magnetic declination estimated value calculator</a> to get a declination, which you can add to your heading.
</details>

The way you go from having an x and a y coordinate to having a heading is by using the function atan2. The Python math docs explain this function very well:

`math.atan2(y, x)`: Return `atan(y / x)`, in radians. The result is between -pi and pi. The vector in the plane from the origin to point `(x, y)` makes this angle with the positive X axis. The point of `atan2()` is that the signs of both inputs are known to it, so it can compute the correct quadrant for the angle. For example, `atan(1)` and `atan2(1, 1)` are both `pi/4`, but `atan2(-1, -1)` is `-3*pi/4`. (--Python docs)

So like this:

<img src="https://upload.wikimedia.org/wikipedia/commons/a/ad/Atan2definition.svg" width="250" alt="atan2(y,x) returns the angle θ between the ray to the point (x,y) and the positive x-axis, confined to (-π, π]."/>

You can then add 2π to all negative values of θ to get reflex angles, which for headings are more conventional.

Note, though, that all this means it matters where the positive y-axis is: θ will be acute or obtuse when y is positive, and negative or reflex when y is negative. So if you look back at the first picture where the positive z-axis points downwards, this means that here, if you take the x-axis as your "nose", then atan2(y, x) actually gives you (2π-heading), not the heading itself.

Conveniently or confusingly, the LSM303DLHC's axis orientation follows the right-hand convention like in the picture, but "upside down", with the z-axis pointing upwards:

<img src="https://cdn-shop.adafruit.com/970x728/1120-00.jpg" width="300" alt="The LSM303DLHC's axis orientation follows the right-hand convention, with the z-axis pointing upwards"/>

This means that you have to decide which way up you are going to use your LSM303DLHC, and if you decide to have it PCB-side-up, which is to say positive-z-axis-side-up, then you _can_ just use `atan2(y, x)` to get your heading. Yay!

