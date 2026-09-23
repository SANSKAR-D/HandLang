# HandLang Formal Grammar (EBNF)

```ebnf
program     ::= statement* RUN

statement   ::= forward
              | turn
              | pen
              | color
              | repeat
              | assign

forward     ::= FORWARD number
turn        ::= TURN number
pen         ::= PEN_TOGGLE
color       ::= COLOR number
repeat      ::= REPEAT number statement* END
assign      ::= VAR NUMBER number       (* VAR <var_id> <value> *)

number      ::= NUMBER                  (* literal integer *)
              | VAR NUMBER              (* variable reference, e.g. VAR 1 → v1 *)
```

## Notes

- **Digits → numbers**: raw `DIGIT_0` … `DIGIT_9` tokens are combined into
  `NUMBER` tokens by the lexer *before* parsing.
- **Variables**: `VAR 1 50` assigns 50 to variable `v1`.
  `FORWARD VAR 1` moves forward by the value stored in `v1`.
- **Blocks**: `REPEAT … END` is the only block construct in v1.
- **IF**: reserved in the token set but not yet in the grammar (stretch goal).
