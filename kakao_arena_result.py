# -*- coding: utf-8 -*-
from collections import Counter

import fire
from tqdm import tqdm

from arena_util import load_json
from arena_util import write_json
from arena_util import remove_seen
from arena_util import most_popular


class GenreMostPopular:
    def _artist_songs(self, song_meta, song_mp_counter):
        art_dic = {}

        all_song_mp = [k for k, v in song_mp_counter.most_common()]

        for sid in all_song_mp:
            for genre in song_meta[sid]["artist_name_basket"]:  # 아티스트 네임 베스킷
                art_dic.setdefault(genre, []).append(sid)  # 키값 : genre , 값 : [sid(sid : 'id')]

        for k, v in list(art_dic.items()):
            if len(v) <= 200:
                del art_dic[k]

        return art_dic

    def _song_mp_per_genre(self, song_meta, global_mp): #song_meta : {int(song["id"]): song for song in song_meta_json}, global_mp : song_mp_counter(가장 많이 나온 곡)
        res = {}

        for sid, song in song_meta.items(): #sid : 'id'
            for genre in song['song_gn_gnr_basket']: #장르 추출
                res.setdefault(genre, []).append(sid) #키값 : genre , 값 : [sid(sid : 'id')]

        for genre, sids in res.items():
            res[genre] = Counter({k: global_mp.get(int(k), 0) for k in sids}) #키값:k(sids), value:global_mp.get(int(k), 0), 해당 장르의 곡 카운트()
            res[genre] = [k for k, v in res[genre].most_common(200)] #genre에 대해 가장 많이 나오는 곡 200개

        return res

    def _songs_most_tag(self, t_content):
        tags = []
        songs = []
        tag_id = {}

        for doc in t_content:
            tags.append(doc['tags'])

        for doc in t_content:
            songs.append(doc['songs'])

        for i in range(len(songs)):
            size = len(songs[i])
            for j in range(size):
                if bool(tag_id.get(songs[i][j])) == False:
                    tag_id.setdefault(songs[i][j], tags[i])
                else:
                    tag_id[songs[i][j]] = tag_id[songs[i][j]] + tags[i]

        return tag_id

    def _tags_most_songs(self, t_content):
        tags = []
        songs = []
        song_id = {}

        for doc in t_content:
            tags.append(doc['songs'])

        for doc in t_content:
            songs.append(doc['tags'])

        for i in range(len(songs)):
            size = len(songs[i])
            for j in range(size):
                if bool(song_id.get(songs[i][j])) == False:
                    song_id.setdefault(songs[i][j], tags[i])
                else:
                    song_id[songs[i][j]] = song_id[songs[i][j]] + tags[i]

        return song_id

    def _generate_answers(self, song_meta_json, train, questions): #train : arena_data/orig/train.json
        song_meta = {int(song["id"]): song for song in song_meta_json} #song id를 키값으로 저장하고 그 song의 특징(tags, name 등) 저장
        song_mp_counter, song_mp = most_popular(train, "songs", 200) #song_mp_counter : 딕셔너리값({... , 18273 : 1, ...}),song_mp : train에서 'songs'에 가장 많이 있는 200개 곡
        tag_mp_counter, tag_mp = most_popular(train, "tags", 100) #train에서 'tags'에 가장 많이 있는 100개 태그
        song_mp_per_genre = self._song_mp_per_genre(song_meta, song_mp_counter) #song_mp_per_genre = res ex) res = { pop : ['hello' : 200 ... ], }
        art_dic = self._artist_songs(song_meta, song_mp_counter) #200넘는곡을 가진 가수의 이름과 곡 딕셔너리
        tag_id = self._songs_most_tag(train)

        answers = []
        for q in tqdm(questions):

            genre_counter = Counter()
            art_c = Counter()
            tag_c = Counter()

            for sid in q["songs"]:
                for genre in song_meta[sid]["artist_name_basket"]:
                    art_c.update({genre: 1})

            artist_name = list(art_c.keys())

            for sid in q["songs"]:
                for genre in song_meta[sid]["song_gn_gnr_basket"]:
                    genre_counter.update({genre: 1})

            top_genre = genre_counter.most_common(1)

            if len(artist_name) == 1 and artist_name[0] in art_dic.keys():
                cur_songs = list(art_dic[artist_name[0]])
            elif len(top_genre) != 0:
                cur_songs = song_mp_per_genre[top_genre[0][0]]
            else:
                cur_songs = song_mp

            tag_list = []

            if (q['songs'] != []):
                for sid in q["songs"]:
                    if (sid in tag_id):
                        for a in tag_id[sid]:
                            tag_c.update({a: 1})
                    tag_list = [k for k, v in tag_c.most_common()]
                if len(tag_list) > 10:
                    cur_tags = tag_list[:10]
                else:
                    new_list = remove_seen(tag_list, tag_mp)[:10]
                    cur_tags = (tag_list + new_list)[:10]
            else:
                cur_tags = remove_seen(q["tags"], tag_mp)[:10]


            answers.append({
                "id": q["id"],
                "songs": remove_seen(q["songs"], cur_songs)[:100],
                "tags": cur_tags
            })

        return answers

    def run(self, song_meta_fname, train_fname, question_fname):
        print("Loading song meta...")
        song_meta_json = load_json(song_meta_fname)

        print("Loading train file...")
        train_data = load_json(train_fname)

        print("Loading question file...")
        questions = load_json(question_fname)

        print("Writing answers...")
        answers = self._generate_answers(song_meta_json, train_data, questions)
        write_json(answers, "results/results.json")


if __name__ == "__main__": #python kakao_arena_result.py run \ --song_meta_fname=res/song_meta.json \ --train_fname=res/train.json \ --question_fname=res/test.json
    fire.Fire(GenreMostPopular)