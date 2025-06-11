import {showNotify} from "vant";

export const notifySuccess = (message: string) => {
    showNotify({
        type: 'success',
        message: message,
        color: '#07c160',
        background: '#e1ffe1',
    });
}

export const notifyWarning = (message: string) => {
    showNotify({
        type: 'warning',
        message: message,
        color: '#e66b1f',
        background: '#e1ffe1',
    });
}


export const notifyError = (message: string) => {
    showNotify({
        type: 'danger',
        message: message,
        color: '#ad0000',
        background: '#ffe1e1',
    });
}
