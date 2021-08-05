 class ExperimentForm(forms.ModelForm):
    """
    This handles the complex experiment forms.

    All internal datasets forms are prefixed with `dataset_`, and all
    internal dataset file fields are prefixed with `file_`. These
    are parsed out of the post data and added to the form as internal
    lists.
    """

    url = forms.CharField(required=False)

    class Meta:
        model = models.Experiment
        fields = ("title", "institution_name", "description")

    class FullExperiment(UserDict):
        """
        This is a dict wrapper that store the values returned from
        the :func:`tardis.tardis_portal.forms.ExperimentForm.save` function.
        It provides a convience method for saving the model objects.
        """

        def save_m2m(self):
            """
            {'experiment': experiment,
            'experiment_authors': experiment_authors,
            'authors': authors,
            'datasets': datasets,
            'datafiles': datafiles}
            """
            self.data["experiment"].save()
            for ae in self.data["experiment_authors"]:
                ae.experiment = self.data["experiment"]
                ae.save()

    def __init__(
        self,
        data=None,
        files=None,
        auto_id="%s",
        prefix=None,
        initial=None,
        error_class=ErrorList,
        label_suffix=":",
        empty_permitted=False,
        instance=None,
        extra=0,
    ):

        super().__init__(
            data=data,
            files=files,
            auto_id=auto_id,
            prefix=prefix,
            initial=initial,
            instance=instance,
            error_class=error_class,
            label_suffix=label_suffix,
            empty_permitted=False,
        )

        # fix up experiment form
        if instance and not data:
            authors = instance.experimentauthor_set.all()
            self.initial["authors"] = ", ".join(
                [self._format_author(a) for a in authors]
            )

        self.experiment_authors = []

        if data:
            self._update_authors(data)

        self.fields["authors"] = MultiValueCommaSeparatedField(
            [author.fields["author"] for author in self.experiment_authors],
            widget=CommaSeparatedInput(
                attrs={
                    "placeholder": "eg. Howard W. Florey, Brian Schmidt "
                    + "(http://nla.gov.au/nla.party-1480342)"
                }
            ),
            help_text="Comma-separated authors and optional emails/URLs",
        )

    def _format_author(self, author):
        if author.email or author.url:
            author_contacts = [author.email, author.url]
            return "%s (%s)" % (
                author.author,
                ", ".join([c for c in author_contacts if c]),
            )
        return author.author

    def _parse_authors(self, data):
        """
        create a dictionary containing each of the sub form types.
        """
        if "authors" not in data:
            return []

        def build_dict(order, author_str):
            author_str = author_str.strip()
            res = {"order": order}
            # check for email (contains @ sign and one dot after)
            email_match = re.match("([^\(]+)\(([^@]+@[^@]+\.[^@]+)\)", author_str)
            if email_match:
                try:
                    author_str, email = email_match.group(1, 2)
                    # Check that it really is a URL
                    email = ExperimentAuthor().fields["email"].clean(email)
                    res["email"] = email
                except ValidationError:
                    pass
            # check for url (any non zero string)
            url_match = re.match("([^\(]+)\(([^\)]+)\)", author_str)
            if url_match:
                try:
                    author_str, url = url_match.group(1, 2)
                    # Check that it really is a URL
                    url = ExperimentAuthor().fields["url"].clean(url)
                    res["url"] = url
                except ValidationError:
                    pass
            res["author"] = author_str.strip()
            return res

        return [build_dict(i, a) for i, a in enumerate(data.get("authors").split(","))]

    def _update_authors(self, data):
        # For each author in the POST in a position
        for author_data in self._parse_authors(data):
            try:
                # Get the current author for that position
                o_ae = self.experiment_authors[author_data["order"]]
                # Update the author form for that position with the new author_data
                self.experiment_authors[author_data["order"]] = ExperimentAuthor(
                    data=author_data, instance=o_ae.instance
                )
            except IndexError:
                # Or create an author for that position
                o_ae = ExperimentAuthor(
                    data=author_data, instance=models.ExperimentAuthor()
                )
                self.experiment_authors.append(o_ae)

    def save(self, commit=True):
        # remove m2m field before saving
        del self.cleaned_data["authors"]

        # fix up experiment form
        if self.instance:
            authors = self.instance.experimentauthor_set.all()
            for author in authors:
                author.delete()

        experiment = super().save(commit)

        authors = []
        experiment_authors = []

        for ae in self.experiment_authors:
            o_ae = ae.save(commit=commit)
            experiment_authors.append(o_ae)

        return self.FullExperiment(
            {
                "experiment": experiment,
                "experiment_authors": experiment_authors,
                "authors": authors,
            }
        )

    def is_valid(self):
        """
        Test the validity of the form, the form may be invalid even if the
        error attribute has no contents. This is because the returnd value
        is dependent on the validity of the nested forms.

        This validity also takes into account forign keys that might be
        dependent on an unsaved model.

        :return: validity
        :rtype: bool
        """
        if self.is_bound and bool(self.errors):
            return not bool(self.errors)

        # TODO since this is a compound field, this should merge the errors
        for ae in self.experiment_authors:
            for name, _ in ae.errors.items():
                if isinstance(ae.fields[name], ModelChoiceField):
                    continue
                if ae.is_bound and bool(ae.errors[name]):
                    return False
        return True
