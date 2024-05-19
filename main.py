import album_meta
from composer import beethoven

def main():
    """
    This is the main function of the audio_meta_tool program.

    This is an example of my recently batch modification of an album's track work metadata.

    It performs the following tasks:
    1. Sets the folder path for the music album.
    2. Generates track work parts for Beethoven piano sonatas.
    4. Updates the track work metadata of the album.
    """

    folder = '/Users/deanliao/Music/Albums/FLAC/Irina Mejoueva/Beethoven; Piano Sonatas, Vol 3, Disc 1'

    track_work_part = beethoven.generate_beethoven_piano_sonatas_tracks([[1, 4],[5, 11], [9, 12]])
    print(track_work_part)
    album_meta.update_track_work(album_meta.read_folder(folder), track_work_part, dry_run=True)

if __name__ == "__main__":
    main()