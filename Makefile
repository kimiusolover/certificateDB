.PHONY: test check-review-gates scan-public

test:
	@python3 -m unittest discover -s tests -p 'test_*.py'

check-review-gates:
	@test -n "$(BASE)" || (echo 'BASE=<git revision> is required' >&2; exit 2)
	@python3 tools/enforce_review_gates.py --base "$(BASE)"

scan-public:
	@python3 tools/scan_public_content.py
