import sys
import json
import datetime


def process_input(input_data, first_timestamp):
    # Extract message body
    message_start = input_data["message"].find("#forsen :") + len("#forsen :")
    message_body = input_data["message"][message_start:]

    # Convert emotes to list of dictionaries
    emotes_list = []
    if "emotes" in input_data and input_data["emotes"]:
        emote_groups = input_data["emotes"].split("/")
        for emote_group in emote_groups:
            emote_id, positions = emote_group.split(":")
            for position in positions.split(","):
                start, end = position.split("-")
                emotes_list.append({"id": emote_id, "start": int(start), "end": int(end)})
    else:
        emotes_list = []  # エモートがない場合は空のリストを使用

    # Split the message into fragments based on emote positions
    fragments = []
    last_end = 0

    if len(emotes_list) == 0:  # エモートがない場合
        fragments.append({
            "text": message_body,
            "emoticon": None
        })
    else:
        # エモートが1つ以上ある場合の処理
        emotes_list.sort(key=lambda x: x["start"])  # エモートのリストを開始位置でソート
        last_end = 0
        for emote_info in emotes_list:
            start, end = emote_info["start"], emote_info["end"]
    
            # Add text before the emote
            if start > last_end:
                fragments.append({
                    "text": message_body[last_end:start],
                    "emoticon": None
                })
    
            # Add the emote with its ID
            fragments.append({
                "text": message_body[start:end+1],
                "emoticon": {
                    "emoticon_id": emote_info["id"]
                }
            })
    
            last_end = end + 1

        # Add remaining text after the last emote, if any
        if last_end < len(message_body):
            fragments.append({
                "text": message_body[last_end:],
                "emoticon": None
            })

    # Construct user badges
    if "badges" in input_data and input_data["badges"]:
        user_badges = [
            {
                "_id": badge.split('/')[0],
                "version": badge.split('/')[1]
            } for badge in input_data["badges"].split(',')
        ]
    else:
        user_badges = []

    # Construct message object
    message = {
        "body": message_body,
        "bits_spent": 0,
        "fragments": fragments,
        "user_badges": user_badges,
        "user_color": input_data["color"] if "color" in input_data and input_data["color"] else None,
        "emoticons": [
            {
                "id": emote_info["id"],
                "begin": emote_info["start"],
                "end": emote_info["end"]
            } for emote_info in emotes_list
        ]
    }

    # Calculate offset seconds
    tmi_sent_ts = int(input_data["tmi-sent-ts"]) / 1000  # Convert to seconds
    if first_timestamp is None:
        first_timestamp = tmi_sent_ts
    offset_seconds = int(tmi_sent_ts - first_timestamp)

    # Construct comment object
    comment = {
        "_id": input_data["id"],
        "created_at": datetime.datetime.utcfromtimestamp(tmi_sent_ts).isoformat() + "Z",
        "channel_id": input_data["room-id"],
        "content_type": "video",
        "content_id": "00000000",
        "content_offset_seconds": offset_seconds,
        "commenter": {
            "display_name": input_data["display-name"],
            "_id": input_data["user-id"],
            "name": input_data["display-name"],
            "bio": "",
            "created_at": datetime.datetime.utcfromtimestamp(tmi_sent_ts).isoformat() + "Z",
            "updated_at": datetime.datetime.utcfromtimestamp(tmi_sent_ts).isoformat() + "Z",
            "logo": ""  # Fill with actual value if available
        },
        "message": message
    }

    return comment, first_timestamp


def main():
    if len(sys.argv) != 2:
        print("Usage: python script.py input.txt")
        return

    input_file = sys.argv[1]
    output_file = input_file.replace(".txt", "_new.json")

    with open(input_file, 'r', encoding='utf-8') as f:
        lines = f.readlines()
        comments = []
        first_timestamp = None
        for line in lines:
            try:
                input_data = {}
                parts = line.split(" :", 1)
                if len(parts) == 2:
                    metadata, message = parts
                    input_data.update(dict(item.split("=") for item in metadata.split(";")))
                    input_data["message"] = message.strip()
                    
                    comment, first_timestamp = process_input(input_data, first_timestamp)
                    comments.append(comment)
            except Exception as e:
                print(f"Error processing line: {line.strip()}")
                print(e)

    output_json = {
        "streamer": {"name": "forsen", "id": comments[0]["channel_id"]} if comments else {},
        "comments": comments,
        "embeddedData": None
    }

    with open(output_file, 'w') as f:
        json.dump(output_json, f, indent=2)


if __name__ == "__main__":
    main()
