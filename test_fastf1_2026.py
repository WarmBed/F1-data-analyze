import fastf1
import traceback

print('fastf1 version:', getattr(fastf1, '__version__', 'unknown'))
print('fastf1 module file:', getattr(fastf1, '__file__', 'unknown'))

if hasattr(fastf1, 'get_event_schedule'):
    print('fastf1.get_event_schedule available')
    try:
        sched = fastf1.get_event_schedule(2026)
        print('Fetched schedule type:', type(sched))
        try:
            import pandas as pd
            if isinstance(sched, pd.DataFrame):
                print('Schedule rows:', len(sched))
                print(sched.head(5).to_dict(orient='records'))
            else:
                print('Schedule repr:', repr(sched)[:400])
        except Exception as e:
            print('Could not introspect schedule:', e)
    except Exception as e:
        print('Error fetching 2026 schedule:', type(e).__name__, e)
        traceback.print_exc()
else:
    print('get_event_schedule not available in installed fastf1')
