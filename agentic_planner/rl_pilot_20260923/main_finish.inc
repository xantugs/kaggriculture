    export('/kaggle/working/last_model.npz')
    evaluate('last_update', '/kaggle/working/last_model.npz', VAL_SEEDS, select=True)
    # The test seeds have not appeared in training, warm-up, or checkpoint selection.
    initial_test = evaluate('test_initial', '/kaggle/working/initial_model.npz', TEST_SEEDS)
    best_test = evaluate('test_selected', '/kaggle/working/best_model.npz', TEST_SEEDS)
    summary = dict(selected_checkpoint=best_label, selection_score=best_score,
                   initial_test={k:v for k,v in initial_test.items() if k != 'rows'},
                   selected_test={k:v for k,v in best_test.items() if k != 'rows'},
                   iterations=len(history), training_transition_count=sum(r['steps'] for r in history),
                   elapsed=round(time.time()-t_start), incumbent='omw_v13f',
                   note='Experimental continuation policy. No competition submission. Codec retains documented limitations.')
    json.dump(summary, open('/kaggle/working/summary.json', 'w'), indent=2)
    print('FINAL', json.dumps(summary), flush=True)
