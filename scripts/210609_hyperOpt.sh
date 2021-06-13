freqtrade hyperopt \
	--hyperopt-loss SharpeHyperOptLossDaily \
	--spaces roi stoploss \
	--strategy Strategy004 \
	--config user_data/configs/210609_slurmHyperopt_test.json \
	-e 100 \
	--dry-run-wallet 1000 \
	--random-state 1337


#freqtrade hyperopt \
#	--hyperopt-loss OnlyProfitHyperOptLoss \
#	--spaces roi stoploss trailing \
#	--strategy Strategy004 \
#	--config user_data/configs/210609_slurmHyperopt_test.json \
#	-e 100 \
#	--dry-run-wallet 1000 \
#	--random-state 1337
#
