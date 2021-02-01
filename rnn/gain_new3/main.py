# -*- coding: utf-8 -*-

import shutil

from core.gain import *
from core.rnn_predic import *
from core.models import *
from core.util import *
#from core.window import WindowGenerator, MissData, make_dataset_water, WaterDataGenerator
from core.window import WindowGenerator, make_dataset_gain, make_dataset_water
from core.file_open import make_dataframe
from core.miss_data import MissData
import json

import os

os.environ["CUDA_DEVICE_ORDER"]="PCI_BUS_ID"   # see issue #152
os.environ["CUDA_VISIBLE_DEVICES"]="0,1"



# input parameter
data_path = 'data/'
parameters_dir = 'input'

parameters_file = 'input.json'
parameters_path = '{dir}/{file}'.format(dir=parameters_dir, file=parameters_file)

#parameters = json.load(parameters_path)
with open(parameters_path, encoding='utf8') as json_file:
    parameters = json.load(json_file)

gain_parameters = parameters['gain']
rnn_parameters = parameters['rnn']
file_parameters = parameters['file']

parameters_path = parameters_dir+'/'+ file_parameters['watershed'] + '.json'
with open(parameters_path, encoding='utf8') as json_file:
    parameters = json.load(json_file)
pd.set_option('display.max_columns', 1000)

data_parameters = parameters['data']

interpolation_option = data_parameters['interpolation']
colum_idx = data_parameters['columns']
watershed = data_parameters['watershed']
file_names = data_parameters['files']
folder = data_parameters['directorys']
for i in range(len(folder)):
    folder[i] = watershed+folder[i]

__GAIN_TRAINING__ = gain_parameters['train']
gain_epochs = gain_parameters['max_epochs']
gain_in_setps = gain_parameters['input_width']
gain_out_setps = gain_parameters['label_width']
gain_batch_size = gain_parameters['batch_size']
gain_fill_no = gain_parameters['fill_width']
gain_shift = gain_parameters['shift_width']
gain_miss_rate = gain_parameters['miss_rate']

__RNN_TRAINING__ = rnn_parameters['train']
rnn_epochs = rnn_parameters['max_epochs']
rnn_in_setps = rnn_parameters['input_width']
rnn_out_steps = rnn_parameters['label_width']
rnn_batch_size = rnn_parameters['batch_size']
rnn_predict_day = rnn_parameters['predict_day']
rnn_target_column = rnn_parameters['target_column']

if rnn_predict_day < 3 or rnn_predict_day >5:
    print('predict_day err')
    exit(88)
rnn_predict_day -= 1


#run_num = [0, 10]
#run_num = [0, 11, 12, 13 ,14 ,15, 16]
run_num = range(len(folder))
#run_num = [0]


real_df_all = pd.DataFrame([])
target_all = target_mean = target_std = 0

gain_val_performance = {}
gain_performance = {}

for i in range(len(run_num)):

    idx = run_num[i]

    print('interpol flag : ', interpolation_option[idx])
    print('folder : ', data_path + folder[idx])
    print('colum_idx : ', colum_idx[idx])
    print('file_names[idx] : ', file_names[idx])

    #start = time.time()

    #if watershed == '한강_12days_test':
    #    df, times = make_dataframe_temp_12days(folder[idx], file_names[idx], colum_idx[idx], interpolate=interpolation_option[idx])
    #else:
    df, times = make_dataframe(data_path+folder[idx], file_names[idx], colum_idx[idx], interpolation=interpolation_option[idx])




    df_all, train_mean, train_std, df = normalize(df)

    print('df_all.shape1233333333333333333333333')
    print(df_all.shape)
    print(len(df))
    print(df[0].shape)

    if i == 0:
        dfff = df
        target_all = df_all
        target_std = train_std
        target_mean = train_mean

    if interpolation_option[idx][0] == False:

        loadfiles = ['idx.npy', 'miss.npy', 'discriminator.h5', 'generator.h5']

        gain_calc_falg = True

        if __GAIN_TRAINING__ == True:
            gain_calc_falg = MissData.save(pd.concat(df, axis=0).to_numpy(), max_tseq=24, save_dir='save/')
            #print(folder[idx], ': training ', 'Miss date save : ', gain_calc_falg)
        else:
            for file in loadfiles:
                if os.path.isfile('save/' + folder[idx]+file):
                    shutil.copyfile('save/' + folder[idx]+file, 'save/'+file)
                    #print('load file name : save/' + folder[idx]+file)
                else:
                    if file == 'miss.npy':
                        gain_calc_falg = MissData.save(pd.concat(df, axis=0).to_numpy(), max_tseq=24, save_dir='save/')
                        #print(folder[idx], ': is not miss.npy ', 'Miss date save : ', gain_calc_falg)

        if gain_calc_falg == True:
            #print('GainWindowGenerator in main')
            WindowGenerator.make_dataset = make_dataset_gain
            wide_window = WindowGenerator(input_width=gain_in_setps, label_width=gain_out_setps, shift=gain_shift,
                                          fill_no=gain_fill_no, miss_rate=gain_miss_rate, batch_size=gain_batch_size,
                                          train_df = df_all, val_df = df_all, test_df = df_all, df = df)

            #gain = model_GAIN(shape=wide_window.dg.shape[1:], gen_sigmoid=False, epochs=gain_epochs, training_flag=__GAIN_TRAINING__, window=wide_window, model_save_path='save/')
            gain = model_GAIN(shape=(gain_in_setps, df_all.shape[1]), gen_sigmoid=False, epochs=gain_epochs,
                              training_flag=__GAIN_TRAINING__, window=wide_window, model_save_path='save/')

            gain_val_performance[str(i)] = gain.evaluate(wide_window.val)
            gain_performance[str(i)] = gain.evaluate(wide_window.test, verbose=0)

            #print('file proc in main')
            if __GAIN_TRAINING__ == True:
                #dir = 'save/'+folder[i]
                if not os.path.exists('save/' + folder[idx]):
                    os.makedirs('save/'+folder[idx])
                for file in loadfiles:
                    shutil.copyfile('save/' + file, 'save/' + folder[idx] + file)

            #print('create_dataset_with_gain in main')
            #ori, gan = create_dataset_with_gain(gain=gain, window=wide_window, df=df)
            ori, gan = create_dataset_with_gain(gain=gain, shape=(gain_in_setps, df_all.shape[1]), df=df)

        else:
            gan = create_dataset_interpol(window=gain_in_setps, df=df)
    else:
        gan = create_dataset_interpol(window=gain_in_setps, df=df)

    if i == 0 :
        real_df_all = pd.DataFrame(gan)
    else:
        real_df_all = pd.concat([real_df_all, pd.DataFrame(gan)], axis=1)


#train_df, val_df, test_df, test_df2 = dataset_slice(real_df_all, 0.8, 0.1, 0.1)
train_df, val_df, test_df, test_df2 = dataset_slice(real_df_all, 0.7, 0.3, 0.0)

print('-------------------prediction')
print('-------------------prediction')
print('-------------------prediction')

print('real_df_all.type : ', type(real_df_all))
print('train_df.type : ', type(train_df))
print('train_df.shape : ', train_df.shape, 'val_df.shape : ', val_df.shape, 'test_df.shape:' ,test_df.shape)


label_columns_indices = {name: i for i, name in enumerate(dfff[0])}

print("label_columns_indices:")
print(label_columns_indices)


print('target columns : ', rnn_target_column)
num_features = dfff[0].shape[1]

target_col_idx = label_columns_indices[rnn_target_column]
out_features = [target_col_idx]
out_num_features = len(out_features)

print("target_col_idx : ", target_col_idx)
print('out_num_features : ', out_num_features)


#print("2021_01_31-21:30:00 --- 삭제해야함")
val_nse = {}
val_pbias = {}



## "save/" + watershed + "models/" + pa[i] +"gru.ckpt" -- path
#for i in range(len(pa)):
#    WindowGenerator.make_dataset = make_dataset_water
#    multi_window = WindowGenerator(
#        input_width=rnn_in_setps, label_width=rnn_out_steps, shift=rnn_out_steps, out_features=[idx[i]],
#        out_num_features=out_num_features, label_columns=dfff[0].columns, batch_size=rnn_batch_size,
#        train_df=train_df, val_df=val_df, test_df=test_df, test_df2=test_df2)
#    print(idx[i], ",,,,,,,,,,,,")
#    print("save/" + watershed + "models/" + pa[i] +"gru.ckpt")
#    gru_model = model_gru(
#        window=multi_window, OUT_STEPS=rnn_out_steps, out_num_features=out_num_features, epochs=rnn_epochs,
#        training_flag=__RNN_TRAINING__, checkpoint_path="save/" + watershed + "models/" + pa[i] +"gru.ckpt")
#
#    val_nse[str(i)], val_pbias[str(i)], pred, label = multi_window.compa(
#        gru_model, plot_col=out_features[0], windows=multi_window.example3,
#        target_std=target_std, target_mean=target_mean, predict_day = rnn_predict_day)
#
#print("2021_01_31-21:30:00 --- 삭제해야함")
#
#
#print("2021_01_31-21:30:00 --- 살려야함 아래아래")
'''
#'''



WindowGenerator.make_dataset = make_dataset_water
multi_window = WindowGenerator(
    input_width=rnn_in_setps,label_width=rnn_out_steps, shift=rnn_out_steps,out_features=out_features,
    out_num_features=out_num_features,label_columns=dfff[0].columns, batch_size=rnn_batch_size,
    train_df=train_df, val_df=val_df, test_df=test_df, test_df2=test_df2)

if __RNN_TRAINING__:
    if not os.path.exists('save/' + watershed):
        os.makedirs('save/' + watershed)


idx = [2, 4, 5, 6, 7]
pa = ["do/", "toc/", "nitrogen/", "phosphorus/", "chlorophyll-a/"]

indices = {name: i for i, name in enumerate(idx)}

model_path = "save/" + watershed + "models/" + pa[indices[target_col_idx]]
print("save model path : ", model_path)

val_nse = {}
val_pbias = {}

 # +"gru.ckpt" -- path

multi_linear_model = model_multi_linear(
    window=multi_window, OUT_STEPS=rnn_out_steps, out_num_features=out_num_features, epochs=rnn_epochs,
    #training_flag=__RNN_TRAINING__, checkpoint_path="save/"+watershed+"models/multi_linear.ckpt")
    training_flag=__RNN_TRAINING__, checkpoint_path=model_path+"multi_linear.ckpt")
elman_model = model_elman(
    window=multi_window, OUT_STEPS=rnn_out_steps, out_num_features=out_num_features, epochs=rnn_epochs,
    training_flag=__RNN_TRAINING__, checkpoint_path=model_path+"elman.ckpt")
gru_model = model_gru(
    window=multi_window, OUT_STEPS=rnn_out_steps, out_num_features=out_num_features, epochs=rnn_epochs,
    training_flag=__RNN_TRAINING__, checkpoint_path=model_path+"gru.ckpt")
multi_lstm_model = model_multi_lstm(
    window=multi_window, OUT_STEPS=rnn_out_steps, out_num_features=out_num_features, epochs=rnn_epochs,
    training_flag=__RNN_TRAINING__, checkpoint_path=model_path+"multi_lstm.ckpt")
multi_conv_model = model_multi_conv(
    window=multi_window, OUT_STEPS=rnn_out_steps, out_num_features=out_num_features, epochs=rnn_epochs,
    training_flag=__RNN_TRAINING__, checkpoint_path=model_path+"multi_conv.ckpt")


val_nse['Linear'], val_pbias['Linear'], pred, label = multi_window.compa(
     multi_linear_model, plot_col=out_features[0], windows=multi_window.example,
     target_std=target_std, target_mean=target_mean, predict_day = rnn_predict_day)
val_nse['ELMAN'], val_pbias['ELMAN'], pred, label = multi_window.compa(
     elman_model, plot_col=out_features[0], windows=multi_window.example3,
     target_std=target_std, target_mean=target_mean, predict_day = rnn_predict_day)
val_nse['GRU'], val_pbias['GRU'], pred, label = multi_window.compa(
     gru_model, plot_col=out_features[0], windows=multi_window.example3,
     target_std=target_std, target_mean=target_mean, predict_day = rnn_predict_day)
val_nse['LSTM'], val_pbias['LSTM'], pred, label = multi_window.compa(
     multi_lstm_model, plot_col=out_features[0], windows=multi_window.example3,
     target_std=target_std, target_mean=target_mean, predict_day = rnn_predict_day)
val_nse['CONV'], val_pbias['CONV'], pred, label = multi_window.compa(
     multi_conv_model, plot_col=out_features[0], windows=multi_window.example3,
     target_std=target_std, target_mean=target_mean, predict_day = rnn_predict_day)

print("save model path : ", model_path)
print('run : ', run_num)
print('tartget : ', rnn_target_column)
print('target col index : ', target_col_idx)
print('Linear : ', val_nse['Linear'])
print('ELMAN : ', val_nse['ELMAN'])
print('GRU : ', val_nse['GRU'])
print('LSTM : ', val_nse['LSTM'])
print('CNN : ', val_nse['CONV'])
print('GAIN_VAL_PER : ', gain_val_performance['0'])
print('GAIN_TEST_PER : ', gain_performance['0'])

#print("2021_01_31-21:30:00 --- 살려야함 위에위에")

x = np.arange(len(val_nse))
width = 0.35
plt.figure()
plt.bar(x, val_pbias.values(), 0.3, label='PBIAS' )
plt.bar(x + width, val_nse.values(), 0.3, label='NSE')
plt.xticks(x,val_nse.keys(), rotation=45)
_ = plt.legend()
plt.show()


#
# multi_val_performance['Linear'] = multi_linear_model.evaluate(multi_window.val.repeat(-1), steps=100)
# multi_performance['Linear'] = multi_linear_model.evaluate(multi_window.test.repeat(-1), verbose=0, steps=100)
#
# multi_val_performance['ELMAN'] = elman_model.evaluate(multi_window.val.repeat(-1), steps=100)
# multi_performance['ELMAN'] = elman_model.evaluate(multi_window.test.repeat(-1), verbose=1, steps=100)
#
# multi_val_performance['GRU'] = gru_model.evaluate(multi_window.val.repeat(-1), steps=100)
# multi_performance['GRU'] = gru_model.evaluate(multi_window.test.repeat(-1), verbose=1, steps=100)
#
# multi_val_performance['LSTM'] = multi_lstm_model.evaluate(multi_window.val)
# multi_performance['LSTM'] = multi_lstm_model.evaluate(multi_window.test, verbose=0)
#
# multi_val_performance['Conv'] = multi_conv_model.evaluate(multi_window.val)
# multi_performance['Conv'] = multi_conv_model.evaluate(multi_window.test, verbose=0)
#multi_window.SetStandMean(std=train_std, mean=train_mean)
#multi_window.compa3(multi_linear_model, plot_col=out_features[0])
#multi_window.plot24(multi_linear_model, plot_col=out_features[0])
#
# x = np.arange(len(multi_performance))
# width = 0.3
# metric_name = 'mean_absolute_error'
# metric_index = multi_conv_model.metrics_names.index('mean_absolute_error')
# val_mae = [v[metric_index] for v in multi_val_performance.values()]
# test_mae = [v[metric_index] for v in multi_performance.values()]
# plt.figure()
# plt.bar(x - 0.17, val_mae, width, label='Validation')
# plt.bar(x + 0.17, test_mae, width, label='Test')
# plt.xticks(ticks=x, labels=multi_performance.keys(), rotation=45)
# plt.ylabel(f'MAE (average over all times and outputs)')
# _ = plt.legend()
# plt.show()




