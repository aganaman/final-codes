import seaborn as sn
import matplotlib.pyplot as plt

data = [[1, 0, 0, -1, -1], [1, 0, 1, 1, -1], [-1, 0, 0, 1, 0], [0, -1, -1, 0, -1], [1, 0, 1, 1, -1]]
# plotting the heatmap
hm = sn.heatmap(data = data, cmap="YlOrRd")
  
# displaying the plotted heatmap
plt.show()