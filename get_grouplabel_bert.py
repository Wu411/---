import pandas as pd
from bert_serving.client import BertClient
import jieba
import numpy as np
import re


#打开自定义词典
with open("stopwords.txt", "r", encoding='utf-8') as f2:
    stopwords = []
    for line in f2.readlines():
        word = line.strip('\n')
        stopwords.append(word)
with open("self_dict.txt", "r", encoding='utf-8') as f2:
    self_dict = []
    for line in f2.readlines():
        word = line.strip('\n')
        self_dict.append(word)

#对自定义词典进行自动更新
def update_selfdict(path):
    df = pd.read_excel(path, sheet_name="event_group")
    data=df['description'].dropna().drop_duplicates().values.tolist()
    for i in data:
        spec_words = re.findall(r'([a-zA-Z][a-zA-Z0-9]+([-_.][a-zA-Z0-9]+)+)', i)
        for i in spec_words:
            if i[0] not in self_dict:
                self_dict.append(i[0])
    with open("self_dict.txt", "w", encoding='utf-8') as f1:
        for i in self_dict:
            f1.writelines(i)
            f1.write('\n')
    return self_dict

#获取各个类别的标签label并分词
def get_group_keyword(path):
    update_selfdict(path)
    df = pd.read_excel(path, sheet_name="event_group")
    data = df.loc[:,['id','description']]
    group = data['id'].values.tolist()
    group_keyword={}
    jieba.load_userdict("self_dict.txt")
    for i in group:
        index=int(i)
        group_keyword[index]=[]
        keywords=data.loc[data['id']==i]['description'].values.tolist()
        for j in keywords:
            for k in jieba.lcut(j):
                if k not in stopwords and k not in group_keyword[index]:
                    group_keyword[index].append(k)

    return group_keyword

def get_bert(dict):
    bc = BertClient()
    output=[]
    for seg_list in dict.values():
        vector = bc.encode(seg_list)
        output.append(vector)#将所有类别的标签label的分词结果转化为词向量

    tmp = [0 for i in range(768)]
    output,maxlen=fill(output,tmp)#将所有类别的标签label分词的词向量个数补齐
    print(type(output))
    with open('group_label_bert.txt', 'w') as outfile:#将所有类别标签label分词的词向量存入文件
        for slice_2d in output:
            np.savetxt(outfile, slice_2d, delimiter=',')
    with open('group_label_bert_size.txt', 'w') as out:#将所有类别标签label分词的词向量的各个维度存入文件
        out.writelines(str(output.shape))
        out.write('\n')
    return output,maxlen

def fill(list_args, fillvalue):#将不同类别标签label分词的词向量个数补齐
    my_len = [len(k) for k in list_args]
    max_num = max(my_len)
    result = []

    for my_list in list_args:
        my_list=my_list.tolist()
        if len(my_list) < max_num:
            for i in range(max_num - len(my_list)):
                my_list.append(fillvalue)
        my_list=np.array(my_list)
        result.append(my_list)
    result=np.array(result)

    return result,max_num

if __name__ == "__main__":
    #当类别的标签发生变化时运行本程序
    path = 'D:\\毕设数据\\数据\\event_group.xls'
    #获取所有类别的标签label的分词结果的字典
    group_label_dict = get_group_keyword(path)
    #获取所有类别的标签label的分词结果的词向量
    group_label_bert, maxlen = get_bert(group_label_dict)

