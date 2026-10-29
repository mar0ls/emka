#!/bin/bash
cd "$(dirname "$0")"
./run.sh
emka_status=$?
if [ "$emka_status" -ne 0 ]; then
  echo "Aplikacja zakończyła się błędem. Naciśnij Enter, aby zamknąć."
  read -r emka_answer
fi
exit "$emka_status"
