# -*- coding: utf-8 -*-
import io
import os
import json
import distutils.dir_util
from collections import Counter

import numpy as np


def write_json(data, fname): #arena_data파일 만들어서 학습,결과 데이터(확장자명 : json) 만들어 줄때 사용하는 함수
    def _conv(o):
        if isinstance(o, (np.int64, np.int32)):
            return int(o)
        raise TypeError

    parent = os.path.dirname(fname)
    distutils.dir_util.mkpath("./arena_data/" + parent)
    with io.open("./arena_data/" + fname, "w", encoding="utf-8") as f:
        json_str = json.dumps(data, ensure_ascii=False, default=_conv)
        f.write(json_str)


def load_json(fname): #json파일 열기 위한 함수
    with open(fname, encoding="utf-8") as f:
        json_obj = json.load(f)

    return json_obj


def debug_json(r):
    print(json.dumps(r, ensure_ascii=False, indent=4))


def remove_seen(seen, l): #중복 없애기위한 함수
    seen = set(seen)
    return [x for x in l if not (x in seen)]


def most_popular(playlists, col, topk_count):
    c = Counter()

    for doc in playlists:
        c.update(doc[col])#doc번째 col요소를 c에 추가한다고 봐주면 됨
        #Counter({'밤편지': 4, '으르렁': 3, '블루밍': 2})

    topk = c.most_common(topk_count)
    return c, [k for k, v in topk] # k:키값, v:딕셔너리값