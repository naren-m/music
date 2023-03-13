import plotly.graph_objs as go
from plotly.subplots import make_subplots

fig = go.FigureWidget()
fig.add_trace(go.Scatter(x=[], y=[], mode='lines+markers'))
fig.show()
def update_plot(fig, data):
    x = list(range(1, len(data)+1))
    y = data
    # Check if the plot already exists

    # Update the existing plot
    fig.data[0].x = list(fig.data[0].x) + x
    fig.data[0].y = list(fig.data[0].y) + y
    fig.update_layout(xaxis_range=[1, len(fig.data[0].x)])


import time, random
while True:
    time.sleep(1)
    update_plot(fig, [random.randint(0, 9)])
