from typer._click.core import ParameterSource
from typer._click.shell_completion import CompletionItem
from typer.core import TyperCommand, TyperOption


class OptionSuggestingCommand(TyperCommand):
    """A TyperCommand that also suggests `--options` on a bare, empty TAB.

    Click (and Typer, which vendors its own copy) only offers option
    flags once the user has typed a leading `-` -- see
    `typer._click.core.Command.shell_complete`, which this mirrors. Once
    every positional argument is already filled, a bare TAB then has
    nothing left to complete and falls through to the shell's native file
    completion -- a confusing directory dump. This suggests the remaining
    options instead, using the same filtering Typer itself would use if
    the incomplete word already started with `-`.
    """

    def shell_complete(self, ctx, incomplete):
        results = super().shell_complete(ctx, incomplete)
        if results or incomplete:
            return results

        for param in self.get_params(ctx):
            if (
                not isinstance(param, TyperOption)
                or param.hidden
                or (
                    not param.multiple
                    and ctx.get_parameter_source(param.name) is ParameterSource.COMMANDLINE
                )
            ):
                continue
            results.extend(
                CompletionItem(name, help=param.help) for name in [*param.opts, *param.secondary_opts]
            )
        return results
