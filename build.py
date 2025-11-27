import os
import shutil
import markdown
import frontmatter
from jinja2 import Environment, FileSystemLoader
from datetime import datetime
import logging
import dotenv

CONTENT_DIR = "content"
OUTPUT_DIR = dotenv.get_key(dotenv_path=".env", key_to_get="OUTPUT_DIR")
TEMPLATE_DIR = "templates"
STATIC_DIR = "static"

SPECIAL_CONTENT = ["Contact Me", "About Me"]

logging.getLogger().setLevel(logging.INFO)


def build() -> None:
    if OUTPUT_DIR is None:
        logging.error("Must set 'OUTPUT_DIR' environment variable")
        exit()
    if os.path.exists(OUTPUT_DIR):
        for item in os.listdir(OUTPUT_DIR):
            item_path = os.path.join(OUTPUT_DIR, item)
            try:
                if os.path.isfile(item_path) or os.path.islink(item_path):
                    os.unlink(item_path)
                elif os.path.isdir(item_path):
                    shutil.rmtree(item_path)
            except Exception as e:
                logging.error(f"Failed to delete {item_path}. Exception: {e}")
    else:
        os.makedirs(OUTPUT_DIR)

    env = Environment(loader=FileSystemLoader(TEMPLATE_DIR))
    post_template = env.get_template("post.html")
    base_template = env.get_template("base.html")

    posts = []

    for filename in os.listdir(CONTENT_DIR):
        if filename.endswith(".md"):
            logging.info(f"Loading '{filename}'")
            post_path = os.path.join(CONTENT_DIR, filename)
            post = frontmatter.load(post_path)

            if post.get("hide"):
                logging.info("Skipping hidden post.")
                continue

            raw_date = post.get("date", datetime.now())
            date_str = str(raw_date)[:10]

            html_content = markdown.markdown(
                post.content,
                extensions=["fenced_code", "codehilite"],
                extension_configs={
                    "codehilite": {
                        "css_class": "highlight",
                        "linenums": False,
                        "guess_lang": False,
                    }
                },
            )

            context = {
                "title": post.get("title", "Untitled"),
                "date": date_str,
                "content": html_content,
                "build_date": datetime.now().strftime("%Y-%m-%d"),
            }

            output_html = post_template.render(context)

            logging.info(f"Rendered '{filename}'")

            output_filename = filename.replace(".md", ".html")
            with open(os.path.join(OUTPUT_DIR, output_filename), "w") as f:
                f.write(output_html)

            posts.append(
                {
                    "title": context["title"],
                    "url": output_filename,
                    "date": context["date"],
                }
            )

    posts.sort(key=lambda x: x["date"], reverse=True)
    posts = list(filter(lambda x: x["title"] not in SPECIAL_CONTENT, posts))

    index_html = base_template.render(
        {
            "title": "Home",
            "build_date": datetime.now().strftime("%Y-%m-%d"),
            "content": "<ul>"
            + "".join(
                [
                    f'<li>{p["date"]} - <a href="{p["url"]}">{p["title"]}</a></li>'
                    for p in posts
                ]
            )
            + "</ul>",
        }
    )

    with open(os.path.join(OUTPUT_DIR, "index.html"), "w") as f:
        f.write(index_html)

    if os.path.exists(STATIC_DIR):
        for item in os.listdir(STATIC_DIR):
            s = os.path.join(STATIC_DIR, item)
            d = os.path.join(OUTPUT_DIR, item)
            if os.path.isdir(s):
                shutil.copytree(s, d)
            else:
                shutil.copy2(s, d)

    logging.info(f"Site built in {OUTPUT_DIR}")


if __name__ == "__main__":
    build()
