from bankagent_shared.redaction import KnownPII, mask_account, mask_mapping, mask_text


class TestRegexMasking:
    def test_masks_10_digit_account_number(self) -> None:
        assert mask_text("my account is 1002345678 thanks") == "my account is ****5678 thanks"

    def test_masks_13_digit_sa_id(self) -> None:
        assert mask_text("ID 9001015009087") == "ID ****9087"

    def test_masks_9_digit_omang(self) -> None:
        assert mask_text("Omang 123456789") == "Omang ****6789"

    def test_sa_id_not_partially_matched_as_account(self) -> None:
        # A 13-digit run must be masked once, not chopped into a 10-digit match.
        out = mask_text("9001015009087")
        assert out == "****9087"

    def test_leaves_short_numbers_alone(self) -> None:
        assert mask_text("card ending 4821, amount 12345") == "card ending 4821, amount 12345"

    def test_amounts_and_dates_untouched(self) -> None:
        text = "R4,899.00 on 2026-06-28"
        assert mask_text(text) == text


class TestKnownValueMasking:
    def test_masks_exact_value(self) -> None:
        known = KnownPII()
        known.add("1002345678")
        assert mask_text("that is 1002345678 yes", known) == "that is ****5678 yes"

    def test_masks_spoken_form_with_spaces(self) -> None:
        known = KnownPII()
        known.add("1002345678")
        assert mask_text("it's 10 0234 5678", known) == "it's ****5678"

    def test_masks_dashed_form(self) -> None:
        known = KnownPII()
        known.add("1002345678")
        assert mask_text("10-0234-5678", known) == "****5678"

    def test_ignores_short_values(self) -> None:
        known = KnownPII()
        known.add("4821")  # card last4 - must NOT be registered
        assert mask_text("ending in 4821", known) == "ending in 4821"

    def test_add_is_idempotent(self) -> None:
        known = KnownPII()
        known.add("1002345678")
        known.add("100 234 5678")
        assert mask_text("1002345678", known) == "****5678"


class TestSpokenNumberMasking:
    """Voice transcripts carry numbers as words - the exact leak a supervisor
    would otherwise read in the transcripts browser."""

    def test_caller_reading_account_number_as_words(self) -> None:
        text = (
            "One, double zero, two three four five six seven eight, "
            "and my ID ends in nine zero eight seven."
        )
        out = mask_text(text)
        assert "****5678" in out  # reconstructed digits keep the usual mask shape
        assert "****" in out.replace("****5678", "", 1)  # the 4-digit ID run fully masked
        assert "seven eight" not in out and "nine zero" not in out

    def test_agent_echoing_number_back_as_words(self) -> None:
        text = (
            "Just to confirm, your account number is one double zero two three "
            "four five six seven eight, and the last four digits of your ID are "
            "nine zero eight seven. Is that correct?"
        )
        out = mask_text(text)
        assert "one double zero" not in out and "eight seven" not in out
        assert "****5678" in out

    def test_four_digit_run_never_reveals_itself(self) -> None:
        # ****last4 of a 4-digit value would be the whole value - must be ****.
        assert mask_text("it ends in nine zero eight seven") == "it ends in ****"

    def test_oh_and_triple_forms(self) -> None:
        # triple one=111, oh=0, two=2, double three=33, seven=7 -> 11102337
        assert mask_text("triple one oh two double three seven") == "****2337"

    def test_separated_single_digits(self) -> None:
        assert mask_text("the code is 4 8 2 9 1 3") == "the code is ****"
        assert mask_text("9-0-8-7 is the end") == "**** is the end"

    def test_conversational_english_untouched(self) -> None:
        for text in (
            "one or two questions about one of my accounts",
            "eighteen thousand four hundred and fifty two rand",
            "twenty twenty six",
            "one two three",  # below the four-token threshold
            "wait one second, two things",
        ):
            assert mask_text(text) == text

    def test_card_last4_spoken_is_masked_by_design(self) -> None:
        # Over-masking a spoken card last4 is accepted; digits stay out of transcripts.
        assert mask_text("the card ending four eight two one") == "the card ending ****"


class TestMaskMapping:
    def test_recurses_dicts_and_lists(self) -> None:
        payload = {
            "account_number": "1002345678",
            "nested": {"note": "ID 9001015009087"},
            "items": ["1002345678", 42, None],
        }
        out = mask_mapping(payload)
        assert out == {
            "account_number": "****5678",
            "nested": {"note": "ID ****9087"},
            "items": ["****5678", 42, None],
        }

    def test_non_string_scalars_pass_through(self) -> None:
        assert mask_mapping({"limit": 5, "ok": True}) == {"limit": 5, "ok": True}


def test_mask_account() -> None:
    assert mask_account("1002345678") == "****5678"
    assert mask_account("10-0234-5678") == "****5678"
    assert mask_account("12") == "****"
