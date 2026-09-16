ACME ?= acme
PRG := build/uber_sound_solution.prg
TEASER_PRG := ARPSID_V965_TEASER_RC1.prg

.PHONY: all verify manifest clean
all: verify

verify: $(PRG) $(TEASER_PRG)
	python3 tools/verify_upload_asset.py
	python3 tools/static_acme_sanity.py
	python3 tools/verify_builder_assertions.py
	python3 tools/project_hygiene.py
	python3 tools/verify_asset_block_fit.py
	python3 tools/verify_megablast_music.py
	python3 tools/verify_megablast_continue_plus.py
	python3 tools/verify_megablast_deep.py
	python3 tools/verify_runtime_6502.py
	python3 tools/verify_arpsid_teaser.py
	python3 tools/verify_glyph_edge_clean.py
	python3 tools/verify_vic_screen_isolation.py
	python3 tools/verify_reproducible_build.py
	python3 tools/final_release_contract.py
	python3 tools/verify_manifest.py

$(PRG): src/uber_intro.asm tools/build_prg_python.py assets/uber_bitmap.bin assets/uber_screen.bin assets/uber_color.bin assets/uber_custom_font.bin
	mkdir -p build
	@if command -v $(ACME) >/dev/null 2>&1; then \
		$(ACME) -f cbm -o build/uber_sound_solution.acme.prg src/uber_intro.asm; \
		python3 tools/build_prg_python.py; \
		cmp build/uber_sound_solution.acme.prg $(PRG); \
		rm -f build/uber_sound_solution.acme.prg; \
		echo "PASS: ACME/Python byte parity"; \
	else \
		echo "WARN: ACME not found; using deterministic Python builder."; \
		python3 tools/build_prg_python.py; \
	fi

$(TEASER_PRG): $(PRG)
	cp $(PRG) $(TEASER_PRG)

manifest:
	python3 tools/generate_manifest.py

clean:
	rm -rf build $(TEASER_PRG)
