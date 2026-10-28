// set_state is how runs get retried too; only let cancellation through.
function cancelOnly(r) {
    let type;
    try {
        type = JSON.parse(r.requestText).state.type.toUpperCase();
    } catch (e) {
        type = null;
    }
    if (type === 'CANCELLING' || type === 'CANCELLED') {
        r.internalRedirect('@prefect');
    } else {
        r.return(403, '{"detail":"Prefect is read-only here, except for cancelling runs"}');
    }
}

export default { cancelOnly };
