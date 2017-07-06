from fiaas_mast.app import create_app


def main():
    app = create_app()
    app.run(host="0.0.0.0", port=int(app.config['PORT']), debug=bool(app.config['DEBUG']))


if __name__ == '__main__':
    main()
