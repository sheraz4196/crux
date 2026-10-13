"""Marked, reversible profile edits; never restore a stale profile backup."""
import re
import shutil
import os
import tempfile
from pathlib import Path

START = '# >>> crux >>>'
END = '# <<< crux <<<'
PATTERN = re.compile(r'^# >>> crux >>>\r?\n.*?^# <<< crux <<<\r?\n?', re.M | re.S)


def block(shell, enhance_commands=False, keep_prompt=False):
    if shell == 'bash':
        # Command substitution is evaluated by Bash after decoding PS1, so prompt
        # data is never evaluated as shell syntax. Existing hooks remain intact.
        body = '''if command -v crux >/dev/null 2>&1; then
  if [ "${_CRUX_ACTIVE:-}" != 1 ]; then
    _CRUX_OLD_PS1=$PS1
    _CRUX_ACTIVE=1
    PS1='$(crux prompt --status "$?" --shell bash 2>/dev/null || printf "%s" "$ " )'
  fi
fi'''
    elif shell == 'zsh':
        body = '''if (( $+commands[crux] )); then
  if [[ ${_CRUX_ACTIVE:-} != 1 ]]; then
    _CRUX_OLD_PS1=$PS1
    _CRUX_ACTIVE=1
    _CRUX_OLD_PROMPT_SUBST=$options[promptsubst]
    setopt promptsubst
    PS1='$(crux prompt --status "$?" --shell zsh 2>/dev/null || print -r -- "%# ")'
  fi
fi'''
    elif shell == 'powershell':
        body = '''if (Get-Command crux -ErrorAction SilentlyContinue) {
  if (-not $global:CruxActive) {
    $global:CruxOldPrompt = $function:prompt
    $global:CruxActive = $true
    function global:prompt {
      $cruxSuccess = $?
      $cruxLastExitCode = $global:LASTEXITCODE
      $cruxCode = if ($cruxSuccess) { 0 } else { 1 }
      try {
        $cruxOutput = & crux prompt --status $cruxCode --shell powershell 2>$null
        if ($LASTEXITCODE -eq 0 -and $cruxOutput) { return ($cruxOutput -join "`n") }
      } catch {} finally { $global:LASTEXITCODE = $cruxLastExitCode }
      if ($global:CruxOldPrompt) { return (& $global:CruxOldPrompt) }
      return "PS $($executionContext.SessionState.Path.CurrentLocation)> "
    }
  }
}'''
    else:
        raise ValueError('Safe automatic integration is available for bash, zsh, and powershell. cmd and Fish remain unchanged.')
    if keep_prompt:
        body = '# crux: prompt=preserved\n'
    if not keep_prompt and shell in ('bash', 'zsh'):
        body += """
if ! alias crux_restore_prompt >/dev/null 2>&1 && ! typeset -f crux_restore_prompt >/dev/null 2>&1; then
  function crux_restore_prompt {
    if [ "${_CRUX_ACTIVE:-}" = 1 ]; then
      PS1=$_CRUX_OLD_PS1
      unset _CRUX_ACTIVE
"""
        if shell == 'zsh':
            body += '      if [[ $_CRUX_OLD_PROMPT_SUBST == off ]]; then unsetopt promptsubst; fi\n'
        body += '    fi\n  }\nfi\n'
    elif not keep_prompt:
        body += """
if (-not (Get-Command crux_restore_prompt -ErrorAction SilentlyContinue)) {
  function global:crux_restore_prompt {
    if ($global:CruxActive) {
      if ($global:CruxOldPrompt) { Set-Item -Path Function:global:prompt -Value $global:CruxOldPrompt }
      else { Remove-Item Function:global:prompt -ErrorAction SilentlyContinue }
      $global:CruxActive = $false
    }
  }
}
"""
    if enhance_commands:
        if shell == 'powershell':
            raise ValueError('Native wrappers are unavailable for PowerShell; use crux git status.')
        body += '\n# crux: native-wrappers=enabled\n'
        body += """
if command -v crux >/dev/null 2>&1; then
  if ! alias cat >/dev/null 2>&1 && ! typeset -f cat >/dev/null 2>&1; then
  function cat {
    local _crux_file
    if [ -t 0 ] && [ -t 1 ] && [ "$#" -gt 0 ]; then
      for _crux_file in "$@"; do
        case "$_crux_file" in
          -*) command cat "$@"; return $? ;;
        esac
        if [ ! -f "$_crux_file" ]; then
          command cat "$@"
          return $?
        fi
      done
      crux _cat -- "$@"
    else
      command cat "$@"
    fi
  }
  fi
  if ! alias git >/dev/null 2>&1 && ! typeset -f git >/dev/null 2>&1; then
  function git {
    if [ -t 0 ] && [ -t 1 ] && [ "$#" -eq 1 ] && [ "$1" = status ]; then
      crux _git status
    else
      command git "$@"
    fi
  }
  fi
  if ! alias ls >/dev/null 2>&1 && ! typeset -f ls >/dev/null 2>&1; then
  function ls {
    if [ -t 0 ] && [ -t 1 ] && [ "$#" -eq 0 ]; then
      crux _ls
    else
      command ls "$@"
    fi
  }
  fi
  if ! alias tree >/dev/null 2>&1 && ! typeset -f tree >/dev/null 2>&1; then
  function tree {
    if [ -t 0 ] && [ -t 1 ] && [ "$#" -eq 0 ]; then
      crux _tree
    else
      command tree "$@"
    fi
  }
  fi
fi"""
    return START + '\n' + body + '\n' + END + '\n'


def read_profile(path):
    path = Path(path)
    if path.is_symlink():
        raise ValueError('Refusing to edit a symlinked profile; specify its real path explicitly.')
    try:
        content = path.read_bytes()
    except FileNotFoundError:
        content = b''
    try:
        text = content.decode('utf-8')
    except UnicodeDecodeError as exc:
        raise ValueError('Profile must be UTF-8; no changes made.') from exc
    if text.count(START) != text.count(END) or text.count(START) > 1:
        raise ValueError('Ambiguous CRUX markers; no changes made.')
    if START in text and not PATTERN.search(text):
        raise ValueError('Malformed CRUX block; no changes made.')
    return text


def edit_profile(path, shell, remove=False, enhance_commands=False, keep_prompt=False):
    path = Path(path)
    text = read_profile(path)
    if remove:
        updated = PATTERN.sub('', text)
    else:
        integration = block(shell, enhance_commands, keep_prompt)
        if START in text:
            if '# crux: original-no-final-newline\n' in text:
                integration = integration.replace(START + '\n', START + '\n# crux: original-no-final-newline\n', 1)
            updated = PATTERN.sub(lambda match: integration, text)
        else:
            # Put the separator inside our block's owned span by requiring a clean
            # line boundary. A missing final newline is restored on removal.
            prefix = '\n' if text and not text.endswith('\n') else ''
            updated = text + prefix + integration
            if prefix:
                updated = updated.replace(START + '\n', START + '\n# crux: original-no-final-newline\n', 1)
    if updated == text:
        return False
    if remove and '# crux: original-no-final-newline\n' in text:
        match = PATTERN.search(text)
        if match and match.start() > 0:
            updated = text[:match.start() - 1] + text[match.end():]
    path.parent.mkdir(parents=True, exist_ok=True)
    backup = path.with_name(path.name + '.crux-backup')
    if backup.is_symlink():
        raise ValueError('Refusing symlinked profile backup; no changes made.')
    if path.exists() and not backup.exists():
        shutil.copy2(path, backup)
    # Replace atomically so a failed write cannot truncate the profile.
    descriptor, temporary = tempfile.mkstemp(prefix='.crux-', dir=path.parent)
    try:
        with os.fdopen(descriptor, 'wb') as stream:
            stream.write(updated.encode('utf-8'))
            stream.flush()
            os.fsync(stream.fileno())
        if path.exists():
            shutil.copymode(path, temporary)
        os.replace(temporary, path)
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)
    return True
