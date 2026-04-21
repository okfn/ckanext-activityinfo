import logging
import click


def setup_cli_logging(verbose=False, logger_name='ckanext.activityinfo'):
    """Attach a logging handler that forwards app logs to click.echo.

    By default captures everything under the extension's package root so CLI
    commands expose HTTP client activity, job progress, selector decisions,
    etc. Returns (handler, logger) so the caller can remove the handler when
    done.
    """
    logger = logging.getLogger(logger_name)
    handler = logging.Handler()
    handler.emit = lambda record: click.echo(f"  {handler.format(record)}")
    handler.setFormatter(logging.Formatter('%(message)s'))
    handler.setLevel(logging.DEBUG if verbose else logging.INFO)
    logger.addHandler(handler)
    logger.setLevel(handler.level)
    return handler, logger
