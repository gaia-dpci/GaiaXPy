import matplotlib.pyplot as plt
import pytest


def _array_str(values: list[float]) -> str:
    return '(' + ', '.join(str(v) for v in values) + ')'


@pytest.fixture(autouse=True)
def auto_close_plotter_tests(request, monkeypatch):
    if request.node.get_closest_marker("plotter"):
        original_show = plt.show

        def show_briefly(*args, **kwargs):
            original_show(block=False)

            # Show the plot for 1 second
            if plt.get_fignums():
                plt.gcf().canvas.start_event_loop(1)

            plt.close("all")

        monkeypatch.setattr(plt, "show", show_briefly)

    yield
    plt.close("all")
