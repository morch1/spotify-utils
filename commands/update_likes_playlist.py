import util

def run(config, playlist_id, other_playlists, check_albums=False, check_followed_artists=False, by_name_part=False):
    spotify = config.spotify
    sp = spotify.sp

    playlisted_tracks = {}

    if check_albums:
        print('getting tracks from saved albums...')
        saved_albums = sp.current_user_saved_albums()
        while saved_albums:
            for album in saved_albums['items']:
                for track in album['album']['tracks']['items']:
                    playlisted_tracks[track['id']] = (track['artists'][0]['id'], util.normalize_name(track['name']))
            saved_albums = sp.next(saved_albums) if saved_albums['next'] else None
    
    if check_followed_artists:
        print('getting followed artists...')
        followed_artists = []
        artists = sp.current_user_followed_artists()['artists']
        while artists:
            for artist in artists['items']:
                followed_artists.append(artist['id'])
            artists = sp.next(artists)['artists'] if artists['next'] else None

    print('getting tracks from playlists...')
    for gpid in other_playlists:
        gp = sp.playlist(gpid)
        songs = gp['tracks']
        while songs:
            for song in songs['items']:
                playlisted_tracks[song['track']['id']] = (song['track']['artists'][0]['id'], song['track']['name'].lower())
            songs = sp.next(songs) if songs['next'] else None

    print('getting saved tracks and comparing...')
    to_add = []
    for artist_ids, track_id, _, track_name in spotify.liked_tracks:
        if check_followed_artists and any(artist in followed_artists for artist in artist_ids):
            continue
        norm_name = util.normalize_name(track_name)
        short_name = util.shorten_name(track_name)
        if not track_id in playlisted_tracks and not any(s1[0] == artist_ids[0] and s1[1] == norm_name for _, s1 in playlisted_tracks.items()) \
            and not (by_name_part and any(s1[0] == artist_ids[0] and (s1[1] in short_name or short_name in s1[1]) for _, s1 in playlisted_tracks.items())):
            to_add.append(track_id)

    to_remove = []
    songs = sp.playlist(playlist_id)['tracks']
    while songs:
        for song in songs['items']:
            if song['track']['id'] in to_add:
                to_add.remove(song['track']['id'])
            else:
                to_remove.append(song['track']['id'])
        songs = sp.next(songs) if songs['next'] else None

    print('updating playlist...')
    if len(to_add) > 0:
        for i in range(0, len(to_add) // 100 + 1):
            sp.playlist_add_items(playlist_id, to_add[i * 100 : (i + 1) * 100])
    if len(to_remove) > 0:
        for i in range(0, len(to_remove) // 100 + 1):
            sp.playlist_remove_all_occurrences_of_items(playlist_id, to_remove[i * 100 : (i + 1) * 100])
    print('added', len(to_add), 'removed', len(to_remove))
