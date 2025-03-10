import numpy as np

# 创建示例数组
arr = np.array([1, 2, 3, 4, 5])

# 方法1：使用切片方式反转
reversed_arr1 = arr[::-1]
print("使用切片反转:", reversed_arr1)

# 方法2：使用np.flip函数反转
reversed_arr2 = np.flip(arr)
print("使用np.flip反转:", reversed_arr2)
