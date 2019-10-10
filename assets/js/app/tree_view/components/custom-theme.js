export default {
    tree: {
        base: {
            listStyle: 'none',
            backgroundColor: '#ffffff',
            margin: 0,
            padding: 0,
            color: '#000000',
            fontSize: '16px',
            fontFamily: 'inherit'
        },
        node: {
            base: {
                position: 'relative',
                padding: '2px'
            },
            link: {
                position: 'relative',
                padding: '0px 5px',
                display: 'block'
            },
            activeLink: {
                // background: '#007aff36'
            },
            toggle: {
                base: {
                    position: 'relative',
                    display: 'inline-block',
                    verticalAlign: 'top',
                    marginLeft: '-5px',
                    height: '24px',
                    width: '24px'
                },
                wrapper: {
                    position: 'absolute',
                    top: '50%',
                    left: '50%',
                    margin: '-7px 0 0 -7px',
                    height: '14px',
                    // display: 'none'
                },
                height: 14,
                width: 14,
                arrow: {
                    fill: '#007bff',
                    strokeWidth: 0
                }
            },
            header: {
                base: {
                    display: 'inline-block',
                    verticalAlign: 'top',
                    color: '#000000',
                    paddingBottom : '2px'
                },
                connector: {
                    width: '2px',
                    height: '12px',
                    borderLeft: 'solid 2px black',
                    borderBottom: 'solid 2px black',
                    position: 'absolute',
                    top: '0px',
                    left: '-21px'
                },
                title: {
                    lineHeight: '24px',
                    verticalAlign: 'middle',
                    fontSize : '18px',
                }
            },
            subtree: {
                listStyle: 'none',
                paddingLeft: '19px',
                fontSize: '16px',
                paddingBottom: '2px'
            },
            loading: {
                color: '#E2C089'
            }
        }
    }
};