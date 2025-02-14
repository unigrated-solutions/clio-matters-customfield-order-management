Coming Soon

Flask app that allows bulk reordering of custom fields that visually shows the impact on all field sets

I tried to implement a function to revert changes made but I haven't figured out a way without it making a call to Clio's api to adjust the display order of every single custom field which would consume unncessary resources. Those functions are commented out in routes/customfields.py. I'm open to any suggestions on how to reimplement them in a more efficient manner. The only reason that its possible to move fields in bulk that are displayed sporadically is lines 324-336 in routes/customfields.py
