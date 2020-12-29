import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import tensorflow as tf

from glob import glob
from tensorflow.keras.layers import Input, Concatenate, Dot, Add, ReLU, Activation
from tensorflow.keras.layers import Dense
from tensorflow.keras.optimizers import Adam

from core.gain import GAIN
from core.gain_data_generator import GainDataGenerator
from core.window_generator import WindowGenerator
from core.utils import *

folder = 'data'
file_names = [['의암호_2017.xlsx'], ['의암호_2018.xlsx'], ['의암호_2019.xlsx']]

df_list, df_full, df_all = createDataFrame(folder, file_names)
ddd = df_list.copy()
standardNormalization(df_list, df_all)

dgen = GainDataGenerator(df_list)

train_df = df_list[0]
val_df = df_list[0]
test_df = df_list[0]

wide_window = WindowGenerator(
    df=df_list,
    train_df=df_all,
    val_df=df_all,
    test_df=df_all,
    input_width=24 * 5,
    label_width=24 * 5,
    shift=0
)
wide_window.plot(plot_col='총질소')  # create dg issue

val_performance = {}
performance = {}

gain = GAIN(shape=wide_window.dg.shape[1:], gen_sigmoid=False)
gain.compile(loss=GAIN.RMSE_loss)
MAX_EPOCHS = 1500


def compile_and_fit(model, window, patience=10):
    early_stopping = tf.keras.callbacks.EarlyStopping(monitor='val_loss',
                                                      patience=patience,
                                                      mode='min')
    model.compile(loss=GAIN.RMSE_loss)

    history = model.fit(window.train,
                        epochs=MAX_EPOCHS,
                        validation_data=window.val,
                        callbacks=[early_stopping])
    return history


history = compile_and_fit(gain, wide_window, patience=MAX_EPOCHS // 5)

val_performance['Gain'] = gain.evaluate(wide_window.val)
performance['Gain'] = gain.evaluate(wide_window.test, verbose=0)
gain.save(save_dir='save')

gain.evaluate(wide_window.test.repeat(), steps=100)
wide_window.plot(gain, plot_col='클로로필-a')

# custom logic
cnt = 0
for df in df_list:
    data = df.to_numpy()
    total_n = len(data)
    unit_shape = wide_window.dg.shape[1:]
    dim = wide_window.dg.shape[1]
    n = (total_n // dim) * dim
    x = data[0:n].copy()
    y_true = data[0:n].copy()
    x_reshape = x.reshape((-1,) + unit_shape)
    isnan = np.isnan(x_reshape)
    isnan = np.isnan(y_true)
    x_remain = data[-wide_window.dg.shape[1]:].copy()
    x_remain_reshape = x_remain.reshape((-1,) + unit_shape)
    x_remain_reshape.shape

    # zero loss is normal because there is no ground truth in the real dataset
    gain.evaluate(x_reshape, y_true.reshape((-1,) + unit_shape))

    y_pred = gain.predict(x_reshape)
    y_remain_pred = gain.predict(x_remain_reshape)
    y_pred = y_pred.reshape(y_true.shape)

    if y_pred.shape[0] != 8760:
        y_remain_pred = y_remain_pred.reshape(x_remain.shape)
        y_pred = np.append(y_pred, y_remain_pred[-(total_n - n):], axis=0)

    # denormalized
    train_mean = df_all.mean()
    train_std = df_all.std()
    y_pred = pd.DataFrame(y_pred)
    y_pred.columns = df_all.columns
    result = y_pred * train_std + train_mean

    # remove_col = ["Day sin", "Day cos", "Year sin", "Year cos"]
    # for col in remove_col:
    #     result.pop(col)
    result.pop("Day sin")
    result.pop("Day cos")
    result.pop("Year sin")
    result.pop("Year cos")

    df_date = pd.DataFrame(df_full[0]['측정날짜'][:len(result.index)])
    result = pd.concat([df_date, result], axis=1)
    result.to_excel('./data/' + file_names[cnt][0][:8] + '_' + str(MAX_EPOCHS) + '_result.xlsx', index=False)
    cnt += 1

# ''' result plt '''
# y_pred.pop("Day sin")
# y_pred.pop("Day cos")
# y_pred.pop("Year sin")
# y_pred.pop("Year cos")
# y_pred = y_pred.values
#
# plot_data = pd.DataFrame(data)
# plot_data.pop(12)
# plot_data.pop(11)
# plot_data.pop(10)
# plot_data.pop(9)
#
# plot_data = plot_data.values
# y_pred[~np.isnan(plot_data)] = np.nan
# n = 8
# plt.figure(figsize=(9,20))
# for i in range(n):
#     #plt.subplot('%d1%d'%(n,i))
#     plt.subplot(811+i)
#     plt.plot(x[:, i])
#     plt.plot(y_pred[:, i])
# plt.show()
