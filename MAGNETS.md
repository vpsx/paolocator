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


### Compensating for tilt

The first picture superposes the positive x and y axes such that they are aligned with geographic North and East, but of course the axes on the actual magnetometer have nothing to do with geographic axes. You _can_ project the vector of Earth's magnetic field onto the plane tangent to the _Earth's_ surface (so, the x-y plane in the picture) and retain all the information needed to determine your heading; this is obviously not the same as saying that you can take the projection of the vector of Earth's magnetic field onto your magnetometer's x-y plane and do the same. The latter is only true if your magnetometer is always going to be level with the Earth's surface. 

<details markdown="1">
<summary>In other words...</summary>
...ignoring the magnetometer's z-axis reading is in general not the same thing as taking the magnetic field vector's projection onto the Earth's x-y plane.
</details>

In all other situations you have to transform one coordinate space into another--your magnetometer's into the Earth's--and then you can project the vector onto the Earth's x-y plane. The information about how the magnetometer's coordinate space relates to the Earth's coordinate space is provided by the LSM303DLHC's accelerometer. 

The accelerometer readings on the LSM303DLHC are in m/s^2 and express (if you are standing still) Earth's gravitational pull. 

<details markdown="1">
<summary>One can think of it as...</summary>
...the vector defined by the three accelerometer readings is the vector orthogonal to the Earth's plane. Or it is "the Earth's z-axis", if you wave your hands a bit. 
</details>

Intuitively: If you hold the accelerometer perfectly level to the ground, then the Earth's gravitational pull should register entirely on the accelerometer's z-axis. If you point the x-axis up a little bit, a little bit of gravity will be felt along the x-axis. Therefore, the answer to the question "How much of Earth's total gravitational pull is being felt along the accelerometer's x-axis?" is a direct expression of how much the x-axis is "pointing up". More generally, "how much gravity is being felt along each axis" precisely tells us "how the accelerometer is oriented in Earth's coordinate space".

The word for "how much the x-axis is pointing up" is _pitch_, and in exact analogy, "how much the y-axis is pointing up" is called _roll_. Pitch and roll (and yaw--the three rotations about the three axes) are expressed as angles. 

<img src="https://upload.wikimedia.org/wikipedia/commons/thumb/0/04/Flight_dynamics_with_text_ortho.svg/1920px-Flight_dynamics_with_text_ortho.svg.png" width="400" alt="Pitch, roll, and yaw in an aircraft"/>

So we have three accelerometer readings, and we want to turn them into pitch and roll angles. Ignoring for a moment the y-axis, because drawing in 3D is hard, here is a very beautiful picture of the situation: 

[TODO: Picture]

We know `x` and `z` directly from the accelerometer readings, and Pythagoras' theorem tells us that `|g| = sqrt(x^2 + z^2)`. (We'll just call it `g`, not `|g|`, for simplicity.) We want to know what `p` is. If we knew `a`, then we could say `p = arcsine(a/x)`, but we don't know `a`. Fortunately, we can figure out what `a/x` is: 

[TODO: Picture]

The two small triangles are similar to the big, whole triangle, so we know `a/x = x/g`. So we have `p = arcsine x/g = arcsine(x/sqrt(x^2 + z^2))`.

This is all in 2D, but the story generalizes directly to 3D--`g` just becomes `sqrt(x^2 + y^2 + z^2)` and `pitch = arcsine(x/sqrt(x^2  + y^2 + z^2))`. By analogous argument, we find that `roll = arcsine(y/sqrt(x^2  + y^2 + z^2))`.

<details markdown="1">
<summary>You can also think of this as normalisation: ...</summary>
...dividing by <code>sqrt(x^2  + y^2 + z^2)</code> is like taking the magnitude of the full gravitational force to be 1, after which you may imagine the <code>g</code> vector as a vector on the unit sphere, and then you can do all the normal trigonometry on each of the axes, using the normalized readings. 
</details>

Now that we know pitch and roll, we know how the accelerometer/magnetometer are oriented in space, so we can transform accelerator/magnetometer coordinates into Earth coordinates, as planned. In fact it is not necessary to literally transform the coordinates and then project the vector onto the x-y plane. From pitch, roll, and the magnetometer readings, we can simply calculate and combine the relevant contributions from each of the three axes. This is a more direct way of achieving the same result. 

With apologies one last time to the y-axis, which we will ignore in the following picture, here is what the magnetometer's x and z axes look like in relation to the Earth's x-y plane. 

[TODO: Picture] 

Here `a` is the part of the magnetic field along Earth's x-axis that is measured by the magnetometer's z-axis, and `b` is the part of the same measured by the magnetometer's x-axis. We see that `a = z sin(pitch)` and `b = x cos(pitch)`. We see also that (since the big arrow is the sum of the two small component arrows) when the x reading is positive, then the z reading must be negative, and inversely when x is negative then z must be positive. So the pitch-compensated x-reading is always `b - a`, or `x cos(pitch) - z sin(pitch)`. By completely analogous argument, the roll-compensated y-reading is `y cos(roll) - z sin(roll)`. 

And those are the tilt-compensated x and y magnetometer values! As stated before, you take `atan2(y, x)` to get a heading within `(-π, π]`, and then you add 2π to the negative values and probably convert to degrees.

Now you can take six random numbers about magnetic flux and gravity, and turn them into a compass heading! :tada: 
