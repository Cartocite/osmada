""" Data Patcthers

They iterate on action querysets and are supposed to fix buggy or bad data.
They thus may modify the data they work on.

For convenience, the interface is given in AbstractPatcher class.
"""

from osmdata.models import Action, Relation


class AbstractPatcher:
    description = "Abstract patcher"

    def patch(self, qs):
        """ Modifies (patches) the QuerySet

        :param qs: the queryset of Action to be patched
        """
        raise NotImplementedError


class FixRemoveOperationMetadata(AbstractPatcher):
    """
    In remove operations, we have the metadata from the latest node
    modification operation. Whereas we would prefer the metadata from the
    remove operation (from the relation). This patcher fixes that as it can.
    """

    description = "Fix Remove operation metadata attribution"

    def _find_previously_owning_relation(self, qs, remove_action):
        """Heuristic to get the relation previously owning the element

        The old version is removed
        """
        # We look only into the same diff
        same_diff_relations = Relation.objects.filter(
            old_for__diff=remove_action.diff_set.first())

        try:
            # The relation that previously contained our element
            return same_diff_relations.get(
                members__element__osmid=remove_action.old.osmid)
        except (Relation.DoesNotExist, Relation.MultipleObjectsReturned):
            return None

    def patch(self, qs):
        remove_actions = qs.filter(type=Action.REMOVE).select_related('report')

        for action in remove_actions:
            relation = self._find_previously_owning_relation(qs, action)
            if relation:
                # Heuristic worked !
                relation_new_version = relation.old_for.new

                # Actual patching : copy metadata from the changeset which
                # removed the element from the relation
                action.new.changeset = relation_new_version.changeset
                action.new.timestamp = relation_new_version.timestamp
                action.new.user = relation_new_version.user
            else:
                # Empty the metadata than keeping misleading metadata
                action.new.changeset = None
                action.new.timestamp = None
                action.new.user = ''
            action.new.save()
