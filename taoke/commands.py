import click

from .models import Feed


@click.command()
@click.argument("feed-id", type=int)
def cli(feed_id):
    feed = Feed.model_validate_feed_id(feed_id)
    click.echo(f"<Feed {feed.title}> loaded")
    with feed.working_dir():
        with open("manifest.json", "wt") as f:
            f.write(feed.model_dump_json(indent=4))

        click.echo("downloading cover...")
        feed.content.get("cover", True)
        click.echo("downloading video...")
        feed.content.get("video", True)
        click.echo("split scenes...")
        feed.split_scenes()


if __name__ == "__main__":
    cli()
