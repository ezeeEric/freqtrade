#uses pairs from config whitelist
freqtrade backtesting \
	--strategy Strategy004 \
	--config user_data/configs/210609_slurmHyperopt_test.json \
	--dry-run-wallet 1000 \
	--timeframe 1m
#	--strategy-path /home/edrechsl/codez/freqtrade/user_data/strategies/examples \
#	--strategy-list Strategy001 Strategy002 Strategy003 Strategy004 \
