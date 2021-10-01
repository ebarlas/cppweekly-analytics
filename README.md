Have you noticed that C++ Weekly YouTube episodes have been getting longer every week?
Me too! 

This repo contains a Python script to plot episode duration over time, 
complete with a linear regression model.

Don't worry! The 13+ hour Doom port to C++ was excluded!

As a bonus, the script also plots the green color channel saturation in the 
episode banner over time.

```bash
export YT_API_KEY=<YouTube API Key>
python cppweekly.py
```

Dependencies:
* `Pillow` - Image processing library
* `matplotlib` - Plotting library
* `google-api-python-client` - YouTube API client library