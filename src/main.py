import time
start_time = time.time()

from functions.filesystem import get_config, make_output_folder
from functions.orbit import calc_look_angle, make_orbits, make_accesses
from functions.errors import check_targets_error, check_sat_num
from functions.targets import make_targets
from functions.postprocessors import postprocess_apd, postprocess_maxgap

def main(debug=False):
    # Read parameters from input file
    config = get_config()

    if config.post_process.run_access:
        # Check targets for errors
        check_targets_error(config)
        # Check sats for errors
        check_sat_num(config)

        # Make a output folder if needed
        make_output_folder()

        # Make orbits
        orb = make_orbits(config, debug)

        # Make Targets
        els, a_f = make_targets(config, debug) # Returns earth locations and file pointers

        # Get payload graze Limit
        graze = calc_look_angle(config, debug)

        # Generate accesses
        make_accesses(config, orb, els, a_f, graze, debug)

    # Postprocess results
    if config.post_process.access_per_day:
        postprocess_apd(config, debug)

    if config.post_process.max_gap:
        postprocess_maxgap(config, debug)

    return None

if __name__ == '__main__':
    main(debug=True)
    print("--- %s seconds ---" % (time.time() - start_time))
